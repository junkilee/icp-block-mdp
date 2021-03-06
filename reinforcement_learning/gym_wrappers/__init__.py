import gym
import numpy as np
from gym.envs.registration import register

ENTRY_POINT_MAP = {
    "cartpole": "gym_wrappers.wrappers:ModifiedCartPoleEnv"
}


def make(
    domain_name,
    task_name,
    idx,
    seed=1,
    start_state_mode=None,
    start_states=None,
    visualize_reward=True,
    from_pixels=False,
    frame_skip=1,
    episode_length=1000,
):
    env_id = "gym_%s_%s_factor_%s_v1" % (domain_name, task_name, idx)

    if from_pixels:
        assert (
            not visualize_reward
        ), "cannot use visualize reward when learning from pixels"

    # shorten episode length
    max_episode_steps = (episode_length + frame_skip - 1) // frame_skip

    if env_id not in gym.envs.registry.env_specs:
        register(
            id=env_id,
            entry_point=ENTRY_POINT_MAP[domain_name],
            kwargs={
                "start_state_mode": start_state_mode,
                "start_states": start_states,
                "seed": seed
            },
            max_episode_steps=max_episode_steps,
        )
    return gym.make(env_id)
