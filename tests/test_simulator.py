from tfrddlsim.rddl import RDDL
from tfrddlsim.parser import RDDLParser
from tfrddlsim.compiler import Compiler
from tfrddlsim.policy import DefaultPolicy
from tfrddlsim.simulator import SimulationCell, Simulator

import numpy as np
import tensorflow as tf

import unittest


class TestSimulationCell(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        parser = RDDLParser()
        parser.build()

        with open('rddl/Reservoir.rddl', mode='r') as file:
            RESERVOIR = file.read()
            cls.rddl1 = parser.parse(RESERVOIR)

        with open('rddl/Mars_Rover.rddl', mode='r') as file:
            MARS_ROVER = file.read()
            cls.rddl2 = parser.parse(MARS_ROVER)

    def setUp(self):
        self.graph1 = tf.Graph()
        self.compiler1 = Compiler(self.rddl1, self.graph1, batch_mode=True)
        self.batch_size1 = 100
        self.policy1 = DefaultPolicy(self.compiler1, self.batch_size1)
        self.cell1 = SimulationCell(self.compiler1, self.policy1, self.batch_size1)

        self.graph2 = tf.Graph()
        self.compiler2 = Compiler(self.rddl2, self.graph2, batch_mode=True)
        self.batch_size2 = 100
        self.policy2 = DefaultPolicy(self.compiler2, self.batch_size2)
        self.cell2 = SimulationCell(self.compiler2, self.policy2, self.batch_size2)

    def test_state_size(self):
        expected = [((8,),), ((3,), (1,), (1,), (1,))]
        cells = [self.cell1, self.cell2]
        for cell, sz in zip(cells, expected):
            state_size = cell.state_size
            self.assertIsInstance(state_size, tuple)
            self.assertTupleEqual(state_size, sz)

    def test_output_size(self):
        cells = [self.cell1, self.cell2]
        for cell in cells:
            output_size = cell.output_size
            state_size = cell.state_size
            action_size = cell.action_size
            self.assertEqual(output_size, (state_size, action_size, 1))

    def test_initial_state(self):
        cells = [self.cell1, self.cell2]
        batch_sizes = [self.batch_size1, self.batch_size2]
        for cell, batch_size in zip(cells, batch_sizes):
            initial_state = cell.initial_state()
            self.assertIsInstance(initial_state, tuple)
            self.assertEqual(len(initial_state), len(cell.state_size))
            for t, shape in zip(initial_state, cell.state_size):
                self.assertIsInstance(t, tf.Tensor)
                expected_shape = [batch_size] + list(shape)
                if len(expected_shape) == 1:
                    expected_shape += [1]
                self.assertListEqual(t.shape.as_list(), expected_shape)

    def test_simulation_step(self):
        horizon = 40
        cells = [self.cell1, self.cell2]
        batch_sizes = [self.batch_size1, self.batch_size2]
        for cell, batch_size in zip(cells, batch_sizes):
            with cell.graph.as_default():
                # initial_state
                initial_state = cell.initial_state()

                # timestep
                timestep = tf.constant(horizon, dtype=tf.float32)
                timestep = tf.expand_dims(timestep, -1)
                timestep = tf.stack([timestep] * batch_size)

                # simulation step
                output, next_state = cell(timestep, initial_state)
                next_state, action, reward = output
                state_size, action_size, reward_size = cell.output_size

                # next_state
                self.assertIsInstance(next_state, tuple)
                self.assertEqual(len(next_state), len(state_size))
                for s, sz in zip(next_state, state_size):
                    self.assertIsInstance(s, tf.Tensor)
                    self.assertListEqual(s.shape.as_list(), [batch_size] + list(sz))

                # action
                self.assertIsInstance(action, tuple)
                self.assertEqual(len(action), len(action_size))
                for a, sz in zip(action, action_size):
                    self.assertIsInstance(a, tf.Tensor)
                    self.assertListEqual(a.shape.as_list(), [batch_size] + list(sz))

                # reward
                self.assertIsInstance(reward, tf.Tensor)
                self.assertListEqual(reward.shape.as_list(), [batch_size, reward_size])


class TestSimulator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        parser = RDDLParser()
        parser.build()

        with open('rddl/Reservoir.rddl', mode='r') as file:
            RESERVOIR = file.read()
            cls.rddl1 = parser.parse(RESERVOIR)

        with open('rddl/Mars_Rover.rddl', mode='r') as file:
            MARS_ROVER = file.read()
            cls.rddl2 = parser.parse(MARS_ROVER)

    def setUp(self):
        self.graph1 = tf.Graph()
        self.compiler1 = Compiler(self.rddl1, self.graph1, batch_mode=True)
        self.batch_size1 = 100
        self.policy1 = DefaultPolicy(self.compiler1, self.batch_size1)
        self.simulator1 = Simulator(self.compiler1, self.policy1, self.batch_size1)

        self.graph2 = tf.Graph()
        self.compiler2 = Compiler(self.rddl2, self.graph2, batch_mode=True)
        self.batch_size2 = 100
        self.policy2 = DefaultPolicy(self.compiler2, self.batch_size2)
        self.simulator2 = Simulator(self.compiler2, self.policy2, self.batch_size1)

    def test_timesteps(self):
        horizon = 40
        simulators = [self.simulator1, self.simulator2]
        batch_sizes = [self.batch_size1, self.batch_size2]
        for simulator, batch_size in zip(simulators, batch_sizes):
            with simulator.graph.as_default():
                timesteps = simulator.timesteps(horizon)
            self.assertIsInstance(timesteps, tf.Tensor)
            self.assertListEqual(timesteps.shape.as_list(), [batch_size, horizon, 1])
            with tf.Session(graph=simulator.graph) as sess:
                timesteps = sess.run(timesteps)
                for t in timesteps:
                    self.assertListEqual(list(t), list(np.arange(horizon-1, -1, -1)))

    def test_trajectory(self):
        horizon = 40
        simulators = [self.simulator1, self.simulator2]
        batch_sizes = [self.batch_size1, self.batch_size2]
        for simulator, batch_size in zip(simulators, batch_sizes):
            # trajectory
            outputs, final_state = simulator.trajectory(horizon)
            states, actions, rewards = outputs
            state_size, action_size, reward_size = simulator.output_size

            # states
            self.assertIsInstance(states, tuple)
            self.assertEqual(len(states), len(state_size))
            for s, sz in zip(states, state_size):
                s = s[0]
                self.assertIsInstance(s, tf.Tensor)
                self.assertListEqual(s.shape.as_list(), [batch_size, horizon] + list(sz))

            # actions
            self.assertIsInstance(actions, tuple)
            self.assertEqual(len(actions), len(action_size))
            for a, sz in zip(actions, action_size):
                a = a[0]
                self.assertIsInstance(a, tf.Tensor)
                self.assertListEqual(a.shape.as_list(), [batch_size, horizon] + list(sz))

            # rewards
            self.assertIsInstance(rewards, tf.Tensor)
            self.assertListEqual(rewards.shape.as_list(), [batch_size, horizon, reward_size])

    def test_simulation(self):
        horizon = 40
        simulators = [self.simulator1, self.simulator2]
        batch_sizes = [self.batch_size1, self.batch_size2]
        for simulator, batch_size in zip(simulators, batch_sizes):
            trajectory, final_state = simulator.trajectory(horizon)
            states, actions, rewards = simulator.run(trajectory)
            state_size, action_size, reward_size = simulator.output_size

            # states
            self.assertIsInstance(states, tuple)
            self.assertEqual(len(states), len(state_size))
            for s, sz in zip(states, state_size):
                s = s[0]
                self.assertIsInstance(s, np.ndarray)
                self.assertListEqual(list(s.shape), [batch_size, horizon] + list(sz))

            # actions
            self.assertIsInstance(actions, tuple)
            self.assertEqual(len(actions), len(action_size))
            for a, sz in zip(actions, action_size):
                a = a[0]
                self.assertIsInstance(a, np.ndarray)
                self.assertListEqual(list(a.shape), [batch_size, horizon] + list(sz))

            # rewards
            self.assertIsInstance(rewards, np.ndarray)
            self.assertListEqual(list(rewards.shape), [batch_size, horizon, reward_size])
