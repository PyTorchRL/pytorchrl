#!/usr/bin/env python3

import os
import time
import torch
import argparse
from pytorchrl.envs import atari_test_env_factory
from pytorchrl.agent.actors import OnPolicyActor, get_feature_extractor
from pytorchrl.utils import LoadFromFile
from pytorchrl.agent.env.env_wrappers import TransposeImage


def enjoy():

    args = get_args()

    # Define single copy of the environment
    env = atari_test_env_factory(env_id=args.env_id, frame_stack=args.frame_stack)
    env = TransposeImage(env)
    env.render()

    # Define agent device and agent
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    policy = OnPolicyActor.create_factory(
        env.observation_space, env.action_space,
        feature_extractor_network=get_feature_extractor(args.nn),
        restart_model=os.path.join(args.log_dir, "model.state_dict"))(device)

    # Define initial Tensors
    obs = env.reset()
    done, episode_reward = 0, False
    rhs = torch.zeros(1, policy.recurrent_hidden_state_size).to(device)

    # Execute episodes
    while not done:

        env.render()
        time.sleep(0.01)
        obs = torch.Tensor(obs).unsqueeze(0).to(device)
        done = torch.Tensor([done]).unsqueeze(0).to(device)
        with torch.no_grad():
            _, clipped_action, _, rhs, _ = policy.get_action(obs, rhs, done, deterministic=False)
        obs, reward, done, info = env.step(clipped_action.squeeze().cpu().numpy())
        episode_reward += reward

        if done:
            print("EPISODE: reward: {}".format(episode_reward), flush=True)
            done, episode_reward = 0, False
            obs = env.reset()

def get_args():
    parser = argparse.ArgumentParser(description='RL')

    # Configuration file
    parser.add_argument('--conf','-c', type=open, action=LoadFromFile)

    args = parser.parse_args()
    return args

if __name__ == "__main__":
    enjoy()
