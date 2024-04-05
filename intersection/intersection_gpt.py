import os
import sys
import json
import time
import argparse

import openai
from dotenv import load_dotenv
from collections import defaultdict



class Car:
    def __init__(self, X: int, Y: int, color: str):
        self.X = X
        self.Y = Y
        self.color = color
        self.reward = 0
        self.playing = True
        self.XUpdate = X
        self.YUpdate = Y
        self.MoveUpdate = "Go"
    
    def set_reward_from_crash(self):
        self.reward -= 5
    
    def set_reward_from_move(self):
        self.reward -= 2
    
    def queue_update(self, X, Y, Move):
        self.XUpdate = X
        self.YUpdate = Y
        self.MoveUpdate = Move
    
    def update_position(self):
        self.X = self.XUpdate
        self.Y = self.YUpdate


class DrivingGame:
    def __init__(self, _system_prompt_str: str, _otherCar_prompt_str: str, _myCar_prompt_str: str, _carList: list[dict[str,str]]):
        # Car list
        self.car_list = [Car(int(_carData["X"]), \
                             int(_carData["Y"]), \
                             str(_carData["color"])) for _carData in _carList]
        # Prompt templates
        self._system_prompt_str = _system_prompt_str
        self._otherCar_prompt_str = _otherCar_prompt_str
        self._myCar_prompt_str = _myCar_prompt_str
        # Number of cars at given coordinates; convenient for checking crash
        self.position_count = defaultdict(int)
        # Outputs
        self.output_txt = ""
        self.output_csv = "Time step, " + "".join(["Color, X, Y, Reward, Move, " for _ in _carList]) + "\n"

    def play(self):
        time_step = 1
        while not self.check_all_cars_not_playing():
            # status at the beginning of the time step
            self.output_txt += f"Time Step {time_step}:\n"
            self.output_csv += f"{time_step}, "
            for car in self.car_list:
                if car.playing:
                    # exit game if needed
                    car.playing = (car.X != 9) if car.color=="green" else (car.Y != 9)

            # check game end
            conclusion_txt = ""
            conclusion_csv = ""
            if self.check_any_car_crash():
                conclusion_txt += "Car crash. Game over.\n"
                conclusion_csv += "\n"
                for car in self.car_list:    car.playing = False
            if self.check_all_cars_not_playing():
                conclusion_txt += "All cars reached the end of the road. Game over.\n"
                conclusion_csv += "\n"
                for car in self.car_list:    car.playing = False
            if time_step > 20:
                conclusion_txt += "Timed out\n"
                conclusion_csv += "\n"
                for car in self.car_list:    car.playing = False

            # Get (and queue) move update
            for car in self.car_list:
                if car.playing:
                    if car.color != "white":
                        Move, X_pos, Y_pos = self.get_openai_response(car)
                    else:
                        Move, X_pos, Y_pos = ("Go", car.X, car.Y + 1)
                    car.queue_update(X_pos, Y_pos, Move)
            
            # Output
            for car in self.car_list:
                if car.playing:
                    self.output_txt += f"{car.color} car: ({car.X}, {car.Y}), {car.reward}\n"
                    self.output_csv += f"{car.color}, {car.X}, {car.Y}, {car.reward}, {car.MoveUpdate}, "
                elif car.MoveUpdate != "Exited":
                    self.output_txt += f"{car.color} car: ({car.X}, {car.Y}), {car.reward}\n"
                    self.output_csv += f"{car.color}, {car.X}, {car.Y}, {car.reward}, , "
                    car.MoveUpdate = "Exited"
                else:
                    self.output_csv += f",,,,, "
            self.output_txt += "\n"
            self.output_csv += "\n"
            for car in self.car_list:
                if car.playing:
                    self.output_txt += f"{car.color} car chose {Move}\n"

            self.output_txt += conclusion_txt + "\n\n"
            self.output_csv += conclusion_csv
            
            # Update position and position_count
            self.position_count = defaultdict(int)
            for car in self.car_list:
                if car.playing:
                    car.update_position()
                    self.position_count[(car.X, car.Y)] += 1
            
            # Update reward
            for car in self.car_list:
                if car.playing:
                    car.set_reward_from_move()
                    if self.check_crash(car):
                        car.set_reward_from_crash()

            # increment time
            time_step += 1

   
    def check_all_cars_not_playing(self):
        for car in self.car_list:
            if car.playing:
                return False
        return True


    def check_any_car_crash(self):
        for car in self.car_list:
            if car.playing and self.check_crash(car):
                return True
        return False


    def check_crash(self, car):
        return self.position_count[(car.X, car.Y)] > 1


    # get ai repsonse without changing anything variables yet
    def get_openai_response(self, myCar: Car) -> tuple[str, int, int]:
        # call as green or red
        # All the otherCars in the list
        otherCar_list = list()
        for car in self.car_list:
            if myCar != car:
                otherCar_list.append(car)

        # chatgpt prompt
        prompt = []
        
        # system prompt
        system_prompt = {
            'role' : 'system', 
            'content' : self._system_prompt_str 
        }
        prompt.append(system_prompt)

        # user prompt
        user_prompt = ""
        
        for otherCar in otherCar_list:
            otherPosition = f"({otherCar.X},{otherCar.Y})" if otherCar.playing else \
                            "somewhere outside this grid, no longer relevant"
            user_prompt += self._otherCar_prompt_str.replace('{otherColor}', otherCar.color) \
                                                    .replace('{otherPosition}', otherPosition)
        
        myPosition = f"({myCar.X},{myCar.Y})"
        user_prompt += self._myCar_prompt_str.replace('{myColor}', myCar.color) \
                                             .replace('{myPosition}', myPosition) \
                                             .replace('{myReward}',str(myCar.reward))
        
        user_prompt = {
            'role' : 'user', 
            'content' : user_prompt
        }
        prompt.append(user_prompt)
       
        # Get AI response
        response = openai.chat.completions.create(
            model='gpt-4',
            messages=prompt,
            temperature=0.1,
            max_tokens=10,
        )
        rspns_text = response.choices[0].message.content

        # analyze response
        rspns_list = rspns_text.strip('()').split(',')
        Move = rspns_list[0]
        X_pos = int(rspns_list[1])
        Y_pos = int(rspns_list[2])
        return Move, X_pos, Y_pos


def simulate_and_output(_system_prompt_str: str, _otherCar_prompt_str: str, _myCar_prompt_str: str, _carList: list[dict[str,str]], 
                          output_file: str, num_sims: int):
    # Accumulated outputs
    accumulated_txt = ""
    accumulated_csv = ""

    for i in range(1, num_sims+1):
        # Outputs
        accumulated_txt += f"=== Sim {i} ===\n"
        accumulated_csv += f"===, Sim {i}, ===\n"

        # Run game
        game = DrivingGame(_system_prompt_str, _otherCar_prompt_str, _myCar_prompt_str, _carList)
        game.play()

        # Outputs
        accumulated_txt += game.output_txt
        accumulated_csv += game.output_csv
        print(f"Simulation {i} done.")
        time.sleep(1)

    # Outputs
    with open(output_file + ".txt", 'w') as f:    f.write(accumulated_txt)
    with open(output_file + ".csv", 'w') as f:    f.write(accumulated_csv)


if __name__ == "__main__":
    # Command line arguments
    parser = argparse.ArgumentParser(
        description='LLM Intersection Simulator')
    parser.add_argument(dest="config_file", type=str, 
        help="Configuration file path")
    parser.add_argument(dest="output_file", type=str, 
        help="Output file path without file extension")
    parser.add_argument(dest="num_sims", type=int, 
        help="Number of simulations")
    
    args = parser.parse_args()
    config_file = args.config_file
    output_file = args.output_file
    num_sims =  args.num_sims

    if not os.path.isfile(config_file):
        sys.exit("Configuration file path is incorrect")

    # Load openai key
    load_dotenv()
    openai.api_key = os.environ['OPENAI_KEY']
    
    # Load config
    with open(config_file, 'r') as f:    config = json.load(f)
    _system_prompt_str = config['system']
    _otherCar_prompt_str = config['otherCar']
    _myCar_prompt_str = config['myCar']
    _carList = config['carList']

    # Simulate and output
    simulate_and_output(_system_prompt_str, _otherCar_prompt_str, _myCar_prompt_str, _carList,
                        output_file, num_sims)