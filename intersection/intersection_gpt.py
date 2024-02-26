import os
import json
import openai
from dotenv import load_dotenv



class Car:
    def __init__(self, X: int, Y: int, color: str):
        self.X = X
        self.Y = Y
        self.color = color
        self.reward = 0

    def set_position(self, X: int, Y: int):
        self.X = X
        self.Y = Y
    
    def set_reward_from_crash(self):
        self.reward -= 5
    
    def set_reward_from_move(self):
        self.reward -= 2


class DrivingGame:
    def __init__(self, _system_prompt_str):
        self.green_car = Car(1, 3, "green")  # Green car moves along X
        self.red_car = Car(3, 1, "red")    # Red car moves along Y
        self._system_prompt_str = _system_prompt_str

    def play(self):
        time_step = 1
        while True:
            # status at the beginning of the time step
            print(f"Time Step {time_step}:")
            print(f"Green Car: ({self.green_car.X}, {self.green_car.Y}), {self.green_car.reward}")
            print(f"Red   Car: ({self.red_car.X}, {self.red_car.Y}), {self.red_car.reward}")
            print('\n')

            # check game end
            if self.green_car.X == 3 and self.red_car.Y == 3:
                print('Car crash. Game over.')
                break
            if self.green_car.X == 5 and self.red_car.Y == 5:
                print(f"Both cars reached the end of the road. Game over.")
                break
            if time_step > 10:
                break

            # Get move & reward
            for my_car in [self.green_car, self.red_car]:
                Move, X_pos, Y_pos = self.get_openai_response(my_car)
                my_car.set_position(X_pos, Y_pos)
                print(f"{my_car.color} car chose {Move}")

            if self.green_car.X == 3 and self.red_car.Y == 3:
                self.green_car.set_reward_from_crash()
                self.red_car.set_reward_from_crash()
            else:
                self.green_car.set_reward_from_move()
                self.red_car.set_reward_from_move()
            
            print('\n')

            # increment time
            time_step += 1

    # get ai repsonse without changing anything variables yet
    def get_openai_response(self, my_car: Car) -> tuple[str, int, int]:
        # call as green or red
        if my_car == self.green_car:
            other_car: Car = self.red_car
        else:
            other_car: Car = self.green_car
        
        # chatgpt prompt
        prompt = []
        
        # system prompt
        system_prompt = {
            'role' : 'system', 
            'content' : self._system_prompt_str 
        }
        prompt.append(system_prompt)

        # message prompt
        _user_prompt_str = f"You are the {my_car.color} car, you are currently at ({my_car.X},{my_car.Y}). The {other_car.color} car is currently at ({other_car.X},{other_car.Y}). Currently your reward is {my_car.reward}. What is your choice of move? What is your position after the move? Reply in the format of only (Move,PosX,PosY)"
        user_prompt = {
            'role' : 'user', 
            'content' : _user_prompt_str
        }
        prompt.append(user_prompt)
        
        # Get AI response
        response = openai.ChatCompletion.create(
            model='gpt-4',
            messages=prompt,
            temperature=0,
            max_tokens=10,
            top_p=1,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        rspns_text = response['choices'][0]['message']['content']

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
    
    game = DrivingGame(_system_prompt_str)
    game.play()