# train_gym.md
🗹 →

### 기본적인 것들
* defaults:
    - agent: sac  # loading sac.yaml file
* env: cartpole   # 기본 환경
* experiment: test_exp  # 실험 이름

### Train 관련된 것들
* num_train_envs: 3        # 
* train_env_start_state_modes:       []
* train_env_start_states: [[], []]
* num_train_steps: 10000
* replay_buffer_capacity: ${num_train_steps}

* ~~train_factors: [1, 3]    # 각 train에 들어가는 것~~
* ~~test_factors: [5]        # 이건 뭐지?~~
* ~~beta: 2                # 이것도 뭔지 몰라.~~
* ~~noise: 0               # dmc2gym에 들어가는 noise값.~~
* ~~noise_dims: 1          # make_env에서 사용됨.~~


num_seed_steps: 5000 # ??? 이게 뭐지?

### Evaluation 관련
* eval_frequency: 100006
* num_eval_episodes: 10

### GPU 관련
* device: cpu

### logger 관련
* log_frequency: 10000
* log_save_tb: true

### video recorder 관련
* save_video: false

### 전체 seed
* seed: 1

### hydra configuration 관련
* hydra:
  * name: ${env}
  * run:
    * dir: ./\${env}/\${agent.name}_\${experiment}
