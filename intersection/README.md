# Intersection Simulation

## How to run
1. Install all the required python modules specified in the `requirement.txt` file. 
2. Go to this directory. 
3. Edit the `.config` file with your prefered prompts in json format.
    ```
    { "system" : "Your system prompt goes here." ,
        "user" : "Your user   prompt goes here." }
    ```

    a. We used [this link](https://www.freeformatter.com/json-escape.html) to convert unicode texts to json-escaped texts.
    
    b. `system` prompt contains the setup of the markov game. 
    - Given: Environment space $S$, action space $A$, and reward function $R$

    c. `user` prompt shows the current observation of agent $i$, and asks what action to choose. 
    - Given: observation $o_i$. 
    - Asks for: action $a_i$
4. Creat an `.env` file with your OpenAI secret key in the format below. 
    ```
    OPENAI_KEY = ##########
    ```
5. Run the main python script. 
    ```
    python main.py
    ```