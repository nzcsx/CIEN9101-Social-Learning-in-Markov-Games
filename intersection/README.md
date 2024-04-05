# Intersection Simulation

## How to run
1. Install all the required python modules specified in the `requirement.txt` file. 
2. Go to this directory. 
3. Edit the `.config` file with your prefered prompts in json format.
    ```
    { 
      "system"   : "Your system prompt text goes here." ,
      "otherCar" : "Your otherCar prompt text goes here.",
      "myCar"    : "Your myCar prompt text goes here.",
      "carList" :  [{  
                       "X" : "1",
                       "Y" : "5", 
                       "color" : "green"
                    }, {
                       "X" : "5", 
                       "Y" : "1", 
                       "color" : "red"
                    }]
    }
    ```
    a. `system` prompt contains the setup of the markov game. 
    - Given: environment space $S$, action space $A$, and reward function $R$

    b. `otherCar` and `myCar` prompts combine to form the `user` prompt, which shows the current observation of agent $i$, and asks what action to choose. 
    - Given: observation $o_i$. 
    - Asking: action $a_i$

    c. `carList` is a list of cars with their color and initial coordinates.

    d. We used [this link](https://www.freeformatter.com/json-escape.html) to convert unicode texts to json-escaped texts.
4. Create an `.env` file with your OpenAI secret key in the format below. 
    ```
    OPENAI_KEY = ##########
    ```
5. Run the python script. There are 3 positional arguments. 
    ```
    python intersection_gpt.py ./config_output_0_bg/.config ./config_output_0_bg/output 5
    ```
    a. The first argument is the configuration file path.

    b. The second argument is the output file path without file extension.

    c. The third argument is the number of simulations to run. 