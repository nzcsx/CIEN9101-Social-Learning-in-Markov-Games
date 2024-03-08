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
        self.playing = True
        self.XUpdate = X
        self.YUpdate = Y
        self.MoveUpdate = "Go"
    
    def set_reward_from_crash(self):
        self.reward -= 5
    
    def set_reward_from_move(self):
        if self.MoveUpdate == "Lane":
            self.reward -= 2
        elif self.MoveUpdate == "Go":
            self.reward -= 2
        elif self.MoveUpdate == "Stop":
            self.reward -=2

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
    def __init__(self, _system_prompt_str: str, _user_prompt_str: str):
        self.green_car = Car(1, 1, "green")  # Green car moves along X=1
        self.red_car = Car(2, 1, "red")    # Red car moves along X=2
        self._system_prompt_str = _system_prompt_str
        self._user_prompt_str = _user_prompt_str

    def play(self):
        time_step = 1
        while True:
            # status at the beginning of the time step
            print(f"Time Step {time_step}:")
            for my_car in [self.green_car, self.red_car]:
                if my_car.playing:
                    print(f"{my_car.color} car: ({my_car.X}, {my_car.Y}), {my_car.reward}")
                    # exit game if needed
                    my_car.playing = (my_car.Y != 5)
            print('\n')

            # check game end
            if self.check_crash():
                print('Car crash. Game over.')
                break
            if not self.green_car.playing and not self.red_car.playing:
                print(f"Both cars reached the end of the road. Game over.")
                break
            if time_step > 10:
                break

            # Get move & reward
            for my_car in [self.green_car, self.red_car]:
                if my_car.playing:
                    Move, X_pos, Y_pos = self.get_openai_response(my_car)
                    my_car.queue_update(X_pos, Y_pos, Move)
                    print(f"{my_car.color} car chose {Move}")
                else:
                    print(f"{my_car.color} car has exited")

            for my_car in [self.green_car, self.red_car]:
                if my_car.playing:
                    my_car.update_position()

            for my_car in [self.green_car, self.red_car]:
                if my_car.playing:
                    if self.check_crash():
                        my_car.set_reward_from_crash()
                    elif self.check_platoon():
                        my_car.set_reward_from_platoon()
                    else:
                        my_car.set_reward_from_move()
            
            print('\n')

            # increment time
            time_step += 1
    
    def check_crash(self):
        return self.green_car.playing == True and \
               self.red_car.playing   == True and \
               self.green_car.X == self.red_car.X and \
               self.green_car.Y == self.red_car.Y
    
    def check_platoon(self):
        return self.green_car.playing == True and \
               self.red_car.playing   == True and \
               self.green_car.X == self.red_car.X and \
               (self.green_car.Y == self.red_car.Y + 3 or \
                self.green_car.Y == self.red_car.Y - 3)

    # get ai repsonse without changing anything variables yet
    def get_openai_response(self, my_car: Car) -> tuple[str, int, int]:
        # call as green or red
        other_car: Car = self.red_car if my_car == self.green_car else self.green_car

        # chatgpt prompt
        prompt = []
        
        # system prompt
        system_prompt = {
            'role' : 'system', 
            'content' : self._system_prompt_str 
        }
        prompt.append(system_prompt)

        # message prompt
        myPosition = f"({my_car.X},{my_car.Y})"
        otherPosition = f"({other_car.X},{other_car.Y})" if other_car.playing else "somewhere outside this grid, no longer relevant"
        user_prompt = {
            'role' : 'user', 
            'content' : self._user_prompt_str.replace('{myColor}', my_car.color)
                                             .replace('{myPosition}', myPosition)
                                             .replace('{otherColor}', other_car.color)
                                             .replace('{otherPosition}', otherPosition)
                                             .replace('{myReward}',str(my_car.reward))
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
    with open('./platoon/.config') as f:    config = json.load(f)
    _system_prompt_str = config['system']
    _user_prompt_str = config['user']
    
    game = DrivingGame(_system_prompt_str, _user_prompt_str)
    game.play()