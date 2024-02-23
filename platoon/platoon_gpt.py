import os
import openai
from dotenv import load_dotenv



class Car:
    def __init__(self, road, grid):
        self.road = road
        self.grid = grid

class PlatoonDrivingGame:
    def __init__(self):
        self.road1 = [0] * 5  # Road 1 with 5 grids
        self.road2 = [0] * 5  # Road 2 with 5 grids
        self.green_car = Car(1, 1)  # Green car starts at Road 1, Grid 1
        self.red_car = Car(2, 1)    # Red car starts at Road 2, Grid 1
        self.reward = 0

    def go(self, car):
        car.grid += 1
        self.reward -= 2

    def stop(self, car):
        self.reward -= 2

    def lane_change(self, car):
        if car.road == 1:
            car.road = 2
        else:
            car.road = 1
        self.reward += 2  # Reward for being in the same lane

    def play(self):
        for time_step in range(1, 6):
            print(f"Time Step {time_step}:")
            print(f"Green Car: Road {self.green_car.road}, Grid {self.green_car.grid}")
            print(f"Red Car: Road {self.red_car.road}, Grid {self.red_car.grid}")

            if self.green_car.grid == 5 and self.red_car.grid == 5 and self.green_car.road == self.red_car.road:
                print(f"Both cars reached Grid 5 on the same road. Game over.")
                break

            # Define your strategy here. Example strategy:
            if self.green_car.road == self.red_car.road:
                self.go(self.green_car)
                self.go(self.red_car)
            else:
                self.lane_change(self.green_car)

            print(f"Reward: {self.reward}\n")



def get_openai_response():
    # chatgpt prompt
    prompt = []
    
    # system prompt
    system_prompt = {
        'role' : 'system', 
        'content' : 'Here is the set up of the question'  # TBChanged
    }
    prompt.append(system_prompt)

    # message prompt
    msg_prompt = {
        'role' : 'user', 
        'content' : 'Here is the status quo of a car' # TBChanged
    }
    prompt.append(msg_prompt)

    # Get AI response
    response = openai.ChatCompletion.create(
        model='model-name-here', # TBChanged
        messages=prompt,
        temperature=1,
        max_tokens=150,
        top_p=1,
        frequency_penalty=1.5,
        presence_penalty=0.2 # ,
        # stop=
    )
    rspns_text = response['choices'][0]['message']['content']
    return rspns_text



if __name__ == "__main__":
    load_dotenv()
    openai.api_key = os.environ['OPENAI_TOKEN']
    game = PlatoonDrivingGame()
    game.play()