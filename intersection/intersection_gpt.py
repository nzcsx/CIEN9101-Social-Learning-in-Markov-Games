import os
import sys
import json
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
        self.output_cvs = ""

    def play(self):
        time_step = 1
        while True:
            # status at the beginning of the time step
            self.output_txt += f"Time Step {time_step}:\n"
            self.output_cvs += f"{time_step}, "
            for my_car in self.car_list:
                if my_car.playing:
                    self.output_txt += f"{my_car.color} car: ({my_car.X}, {my_car.Y}), {my_car.reward}\n"
                    self.output_cvs += f"{my_car.color}, {my_car.X}, {my_car.Y}, {my_car.reward}, "
                    # exit game if needed
                    my_car.playing = (my_car.X != 9) if my_car.color=="green" else (my_car.Y != 9)
                else:
                    self.output_cvs += f",,,, "
            self.output_txt += "\n"

            # check game end
            if self.check_any_car_crash():
                self.output_txt += "Car crash. Game over.\n\n\n"
                self.output_cvs += "\n\n"
                break
            if self.check_all_car_not_playing():
                self.output_txt += "Both green and red cars reached the end of the road. Game over.\n\n\n"
                self.output_cvs += "\n\n"
                break
            if time_step > 25:
                break

            # Get (and queue) move update
            for my_car in self.car_list:
                if my_car.playing:
                    if my_car.color != "white":
                        Move, X_pos, Y_pos = self.get_openai_response(my_car)
                    else:
                        Move ="Go"
                        X_pos = my_car.X
                        Y_pos = my_car.Y + 1
                    my_car.queue_update(X_pos, Y_pos, Move)
                    self.output_txt += f"{my_car.color} car chose {Move}\n"
                else:
                    self.output_txt += f"{my_car.color} car has exited\n"
            
            # Update position and position_count
            self.position_count = defaultdict(int)
            for my_car in self.car_list:
                if my_car.playing:
                    my_car.update_position()
                    self.position_count[(my_car.X, my_car.Y)] += 1
            
            # Update reward
            for my_car in self.car_list:
                if my_car.playing:
                    my_car.set_reward_from_move()
                    if self.check_crash(my_car):
                        my_car.set_reward_from_crash()
            
            self.output_txt += "\n\n"
            self.output_cvs += "\n"

            # increment time
            time_step += 1
    
    def check_all_car_not_playing(self):
        for my_car in self.car_list:
            if my_car.playing:
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
    def get_openai_response(self, my_car: Car) -> tuple[str, int, int]:
        # call as green or red
        # All the other_cars in the list
        other_car_list = list()
        for car in self.car_list:
            if my_car != car:
                other_car_list.append(car)

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
        
        for other_car in other_car_list:
            other_position = f"({other_car.X},{other_car.Y})" if other_car.playing else \
                            "somewhere outside this grid, no longer relevant"
            user_prompt += self._otherCar_prompt_str.replace('{otherColor}', other_car.color) \
                                                    .replace('{otherPosition}', other_position)
        
        my_position = f"({my_car.X},{my_car.Y})"
        user_prompt += self._myCar_prompt_str.replace('{myColor}', my_car.color) \
                                             .replace('{myPosition}', my_position) \
                                             .replace('{myReward}',str(my_car.reward))
        
        user_prompt = {
            'role' : 'user', 
            'content' : user_prompt
        }
        prompt.append(user_prompt)
       
        # Get AI response
        response = openai.chat.completions.create(
            model='gpt-4',
            messages=prompt,
            temperature=0.0,
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
        accumulated_csv += f"===, Sim {i}, ===\nTime step, "
        for _ in (_carList):    accumulated_csv += "Color, X, Y, Reward, "
        accumulated_csv += "\n"

        # Run game
        game = DrivingGame(_system_prompt_str, _otherCar_prompt_str, _myCar_prompt_str, _carList)
        game.play()

        # Outputs
        accumulated_txt += game.output_txt
        accumulated_csv += game.output_cvs

    # Outputs
    with open(output_file + ".txt", 'w') as f:    f.write(accumulated_txt)
    with open(output_file + ".csv", 'w') as f:    f.write(accumulated_csv)


if __name__ == "__main__":
    # Command line arguments
    parser = argparse.ArgumentParser(
        description='LLM Intersection Simulator')
    parser.add_argument(dest="config_file", type=str, 
        help="Configuration file with json content")
    parser.add_argument(dest="output_file", type=str, 
        help="Output filename without file extension")
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