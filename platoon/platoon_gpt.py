import os
import json
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
        if self.MoveUpdate == "Lane":
            self.reward -= 5
        elif self.MoveUpdate == "Go":
            self.reward -= 2
        elif self.MoveUpdate == "Stop":
            self.reward -= 2

    def set_reward_from_platoon(self):
        self.reward += 2
    
    def queue_update(self, X, Y, Move):
        self.XUpdate = X
        self.YUpdate = Y
        self.MoveUpdate = Move
    
    def update_position(self):
        self.X = self.XUpdate
        self.Y = self.YUpdate


class DrivingGame:
    def __init__(self, _system_prompt_str: str, _otherCar_prompt_str: str, _myCar_prompt_str: str):
        # Parameters
        self.car_list = [Car(1, 1, "green"), Car(2, 1, "red"), Car(1, 2, "white")]
        self.road_length = 9
        self.platoon_spacing = 3
        # Prompt templates
        self._system_prompt_str = _system_prompt_str
        self._otherCar_prompt_str = _otherCar_prompt_str
        self._myCar_prompt_str = _myCar_prompt_str
        # Number of cars at given coordinates; convenient for checking crash
        self.position_count = defaultdict(int)

    def play(self):
        time_step = 1
        while True:
            # status at the beginning of the time step
            print(f"Time Step {time_step}:")
            for my_car in self.car_list:
                if my_car.playing:
                    print(f"{my_car.color} car: ({my_car.X}, {my_car.Y}), {my_car.reward}")
                    # exit game if needed
                    my_car.playing = (my_car.Y != self.road_length)
            print('\n')

            # check game end
            if self.check_any_car_crash():
                print('Car crash. Game over.')
                break
            if self.check_all_car_not_playing():
                print(f"Both green and red cars reached the end of the road. Game over.")
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
                    print(f"{my_car.color} car chose {Move}")
                else:
                    print(f"{my_car.color} car has exited")

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
                    if self.check_platoon(my_car):
                        my_car.set_reward_from_platoon()
            
            print('\n')

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
    
    def check_any_car_platoon(self):
        platoon_dict = defaultdict(bool)
        for car in self.car_list:
            if car.playing and self.check_platoon(car):
                platoon_dict[car.X] = True
        return platoon_dict
    
    def check_platoon(self, car):
        for Y in range(car.Y - self.platoon_spacing, 
                       car.Y + self.platoon_spacing + 1):
            if Y != car.Y and self.position_count[(car.X, Y)]:
                return True
        return False

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
            temperature=0,
            max_tokens=10,
            top_p=1,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        rspns_text = response.choices[0].message.content

        # analyze response
        rspns_list = rspns_text.strip('()').split(',')
        Move = rspns_list[0]
        X_pos = int(rspns_list[1])
        Y_pos = int(rspns_list[2])
        return Move, X_pos, Y_pos


if __name__ == "__main__":
    # load openai key
    load_dotenv()

    openai.api_key = os.environ['OPENAI_KEY']
    
    # load config
    with open('.config') as f:    config = json.load(f)
    _system_prompt_str = config['system']
    _otherCar_prompt_str = config['otherCar']
    _myCar_prompt_str = config['myCar']
    
    game = DrivingGame(_system_prompt_str, _otherCar_prompt_str, _myCar_prompt_str)
    game.play()