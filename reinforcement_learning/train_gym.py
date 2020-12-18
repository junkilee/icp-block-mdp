import time
import os

import torch

import hydra
from .utils import set_seed_everywhere, make_env, eval_mode
from .logger import Logger
from .replay_buffer import MultiEnvReplayBuffer
from .video import VideoRecorder


class Workspace(object):
    def __init__(self, cfg):
        # set work directory
        self.work_dir = os.getcwd()
        print(f"workspace: {self.work_dir}")

        self.cfg = cfg

        # set logger
        self.logger = Logger(
            self.work_dir,
            save_tb=cfg.log_save_tb,
            log_frequency=cfg.log_frequency,
            agent=cfg.agent.name,
        )

        # set seed, device
        set_seed_everywhere(cfg.seed)
        self.device = torch.device(cfg.device)
        # make environment
        self.train_envs, self.test_envs = make_env(cfg)

        # get noise dimension and set agent's observation dimension
        if cfg.noise_dims == -1:
            cfg.noise_dims = self.train_envs[0].observation_space.shape[0]
        cfg.agent.params.obs_dim = (
            self.train_envs[0].observation_space.shape[0] + cfg.noise_dims + 1
        )
        # set action dimension and range of agent
        cfg.agent.params.action_dim = self.train_envs[0].action_space.shape[0]
        if cfg.agent.name != "sac":
            cfg.agent.params.num_envs = cfg.num_train_envs
        cfg.agent.params.action_range = [
            float(self.train_envs[0].action_space.low.min()),
            float(self.train_envs[0].action_space.high.max()),
        ]
        # instantiate agent
        self.agent = hydra.utils.instantiate(cfg.agent)

        # setup replay buffer
        self.replay_buffer = MultiEnvReplayBuffer(
            (cfg.agent.params.obs_dim,),  # hard coded
            self.train_envs[0].action_space.shape,
            int(cfg.replay_buffer_capacity),
            self.device,
            num_envs=cfg.num_train_envs,
        )

        # setup video recorder
        self.video_recorder = VideoRecorder(self.work_dir if cfg.save_video else None)
        # ??
        self.step = [0] * cfg.num_train_envs

    def evaluate(self, env, train=False):
        for episode in range(self.cfg.num_eval_episodes):
            obs = env.reset()
            self.agent.reset()
            self.video_recorder.init(enabled=(episode == 0))
            done = False
            episode_reward = 0
            while not done:
                with eval_mode(self.agent):
                    action = self.agent.act(obs, sample=False)
                obs, reward, done, _ = env.step(action)
                self.video_recorder.record(env)
                episode_reward += reward

            self.video_recorder.save(f"{self.step}.mp4")
            if train:
                self.logger.log(
                    "eval/train_episode_reward", episode_reward, self.step[0]
                )
            else:
                self.logger.log(
                    "eval/eval_episode_reward", episode_reward, self.step[0]
                )

    def run(self):
        episode, episode_reward, episode_step, done = (
            [0] * self.cfg.num_train_envs,
            [0] * self.cfg.num_train_envs,
            [0] * self.cfg.num_train_envs,
            [True] * self.cfg.num_train_envs,
        )
        obs, next_obs = (
            [self.train_envs[0].reset()] * self.cfg.num_train_envs,
            [self.train_envs[0].reset()] * self.cfg.num_train_envs,
        )
        start_time = time.time()
        while self.step[0] < self.cfg.num_train_steps:
            for e_idx, env in enumerate(self.train_envs):
                if done[e_idx]:
                    if self.step[e_idx] > 0:
                        self.logger.log(
                            "train/duration", time.time() - start_time, self.step[e_idx]
                        )
                        start_time = time.time()
                        self.logger.dump(
                            self.step[e_idx],
                            save=(self.step[e_idx] > self.cfg.num_seed_steps),
                        )

                    # evaluate agent periodically
                    if self.step[0] > 0 and self.step[0] % self.cfg.eval_frequency == 0:
                        self.logger.log(
                            "eval/episode", episode[e_idx], self.step[e_idx]
                        )
                        self.evaluate(env, train=True)
                        self.evaluate(self.test_envs[0], train=False)
                        self.logger.dump(self.step[e_idx])
                    self.logger.log(
                        "train/episode_reward", episode_reward[e_idx], self.step[e_idx]
                    )

                    obs[e_idx] = env.reset()
                    self.agent.reset()
                    done[e_idx] = False
                    episode_reward[e_idx] = 0
                    episode_step[e_idx] = 0
                    episode[e_idx] += 1

                    self.logger.log("train/episode", episode[e_idx], self.step[e_idx])

                # sample action for data collection
                if self.step[e_idx] < self.cfg.num_seed_steps:
                    action = env.action_space.sample()
                else:
                    with eval_mode(self.agent):
                        action = self.agent.act(obs[e_idx], sample=True)

                # run training update
                if self.step[e_idx] >= self.cfg.num_seed_steps:
                    self.agent.update(self.replay_buffer, self.logger, self.step[e_idx])

                try:
                    next_obs[e_idx], reward, done[e_idx], _ = env.step(action)
                except:
                    next_obs[e_idx] = obs[e_idx]
                    reward = 0
                    print("Invalid action. Terminating episode.")
                    done[e_idx] = True

                # allow infinite bootstrap
                done[e_idx] = float(done[e_idx])
                done_no_max = (
                    0
                    if episode_step[e_idx] + 1 == env._max_episode_steps
                    else done[e_idx]
                )
                episode_reward[e_idx] += reward

                self.replay_buffer.add(
                    e_idx,
                    obs[e_idx],
                    action,
                    reward,
                    next_obs[e_idx],
                    done[e_idx],
                    done_no_max,
                )

                obs[e_idx] = next_obs[e_idx]
                episode_step[e_idx] += 1
                self.step[e_idx] += 1


@hydra.main(config_path="config/train.yaml", strict=True)
def main(cfg):
    workspace = Workspace(cfg)
    workspace.run()


if __name__ == "__main__":
    main()
