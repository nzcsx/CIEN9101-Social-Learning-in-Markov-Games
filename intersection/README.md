# Intersection Simulation

## How to run
1. Install all the required python modules specified in the `requirement.txt` file. 
2. Go to this directory. 
3. Edit the `.config` file with your prefered prompts in json format.
    ```
    { "system"   : "Your system prompt text goes here." ,
      "otherCar" : "Your otherCar prompt text goes here.",
      "myCar"    : "Your myCar prompt text goes here." }
    ```
    a. `system` prompt contains the setup of the markov game. 
    - Given: environment space $S$, action space $A$, and reward function $R$

    b. `otherCar` and `myCar` prompts combine to form the `user` prompt, which shows the current observation of agent $i$, and asks what action to choose. 
    - Given: observation $o_i$. 
    - Asking: action $a_i$

    c. We used [this link](https://www.freeformatter.com/json-escape.html) to convert unicode texts to json-escaped texts.
4. Create an `.env` file with your OpenAI secret key in the format below. 
    ```
    OPENAI_KEY = ##########
    ```
5. Run the python script. 
    ```
    python intersection_gpt.py
    ```