"""Tests for the trajectory module."""

from agenticrl.trajectory import TrajectoryBuffer, TrajectoryCollector


class TestTrajectoryBuffer:
    """Test the TrajectoryBuffer."""

    @staticmethod
    def _make_traj(total_reward: float, steps: int) -> dict:
        return {
            "observations": ["obs"] * steps,
            "actions": ["act"] * steps,
            "rewards": [1.0] * steps,
            "dones": [False] * (steps - 1) + [True],
            "infos": [{}] * steps,
            "total_reward": total_reward,
            "steps": steps,
        }

    def test_add_and_len(self) -> None:
        """Test adding trajectories and checking length."""
        buffer = TrajectoryBuffer(capacity=10)
        assert len(buffer) == 0
        buffer.add(self._make_traj(5.0, 5))
        assert len(buffer) == 1

    def test_capacity_fifo(self) -> None:
        """Test that buffer respects capacity (FIFO)."""
        buffer = TrajectoryBuffer(capacity=3)
        for i in range(5):
            buffer.add(self._make_traj(float(i), 1))
        assert len(buffer) == 3
        assert buffer.get_all()[0]["total_reward"] == 2.0  # Oldest preserved is index 2

    def test_sample(self) -> None:
        """Test sampling from buffer."""
        buffer = TrajectoryBuffer(capacity=10, seed=42)
        for i in range(5):
            buffer.add(self._make_traj(float(i), 1))
        batch = buffer.sample(2)
        assert len(batch) == 2

    def test_sample_more_than_buffer(self) -> None:
        """Test sampling more than available returns all."""
        buffer = TrajectoryBuffer(capacity=10)
        buffer.add(self._make_traj(1.0, 1))
        batch = buffer.sample(5)
        assert len(batch) == 1

    def test_clear(self) -> None:
        """Test clearing the buffer."""
        buffer = TrajectoryBuffer(capacity=10)
        buffer.add(self._make_traj(1.0, 1))
        buffer.clear()
        assert len(buffer) == 0

    def test_stats(self) -> None:
        """Test statistics computation."""
        buffer = TrajectoryBuffer(capacity=10)
        buffer.add(self._make_traj(3.0, 3))
        buffer.add(self._make_traj(5.0, 2))
        stats = buffer.stats()
        assert stats["mean_reward"] == 4.0
        assert stats["max_reward"] == 5.0
        assert stats["min_reward"] == 3.0
        assert stats["mean_episode_length"] == 2.5
        assert stats["num_episodes"] == 2

    def test_stats_empty(self) -> None:
        """Test stats on empty buffer."""
        buffer = TrajectoryBuffer()
        stats = buffer.stats()
        assert stats["num_episodes"] == 0
        assert stats["mean_reward"] == 0.0

    def test_to_trl_format(self) -> None:
        """Test conversion to TRL format."""
        buffer = TrajectoryBuffer(capacity=10)
        buffer.add({
            "observations": ["What is 2+2?"],
            "actions": ["4"],
            "rewards": [1.0],
            "dones": [True],
            "infos": [{}],
            "total_reward": 1.0,
            "steps": 1,
        })
        trl_data = buffer.to_trl_format()
        assert len(trl_data) == 1
        assert trl_data[0]["prompt"] == "What is 2+2?"
        assert trl_data[0]["completion"] == "4"
        assert trl_data[0]["reward"] == 1.0
