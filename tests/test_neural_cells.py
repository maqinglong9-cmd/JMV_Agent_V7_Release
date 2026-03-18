"""真实神经网络单元测试：Neuron / NeuralLayer / SynapticNetwork / text_to_features"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.cells import (
    _sigmoid, _lcg, _init_weights, text_to_features,
    Neuron, NeuralLayer, SynapticNetwork, GlialCell, CerebrospinalFluid,
)


class TestSigmoid:
    def test_sigmoid_zero(self):
        assert abs(_sigmoid(0.0) - 0.5) < 1e-9

    def test_sigmoid_positive(self):
        assert _sigmoid(10.0) > 0.99

    def test_sigmoid_negative(self):
        assert _sigmoid(-10.0) < 0.01

    def test_sigmoid_range(self):
        for x in [-100, -1, 0, 1, 100]:
            v = _sigmoid(x)
            assert 0.0 <= v <= 1.0


class TestLCG:
    def test_returns_float_and_seed(self):
        r, s = _lcg(42)
        assert isinstance(r, float)
        assert isinstance(s, int)
        assert 0.0 <= r < 1.0

    def test_deterministic(self):
        r1, _ = _lcg(1234)
        r2, _ = _lcg(1234)
        assert r1 == r2

    def test_different_seeds_different_output(self):
        r1, _ = _lcg(1)
        r2, _ = _lcg(2)
        assert r1 != r2


class TestInitWeights:
    def test_returns_correct_length(self):
        w = _init_weights(42, 8)
        assert len(w) == 8

    def test_values_in_xavier_range(self):
        import math
        n = 8
        scale = 1.0 / math.sqrt(n)
        w = _init_weights(42, n)
        for v in w:
            assert -scale <= v <= scale

    def test_deterministic(self):
        w1 = _init_weights(99, 5)
        w2 = _init_weights(99, 5)
        assert w1 == w2


class TestTextToFeatures:
    def test_returns_8_dims(self):
        f = text_to_features("hello")
        assert len(f) == 8

    def test_empty_text_all_zeros(self):
        f = text_to_features("")
        assert all(v == 0.0 for v in f)

    def test_values_in_range(self):
        f = text_to_features("看见光亮闪烁的星星")
        for v in f:
            assert 0.0 <= v <= 1.0

    def test_visual_text_activates_visual_dim(self):
        f_visual = text_to_features("红色闪烁的光")
        f_audio = text_to_features("钢琴旋律和声音")
        # 视觉文本的视觉维度(0)应高于听觉文本的视觉维度
        assert f_visual[0] >= f_audio[0]

    def test_audio_text_activates_audio_dim(self):
        f_audio = text_to_features("钢琴旋律节奏音乐")
        f_visual = text_to_features("红色星星图画")
        # 听觉文本的听觉维度(1)应高于视觉文本的听觉维度
        assert f_audio[1] >= f_visual[1]

    def test_urgent_text_activates_urgency_dim(self):
        f_urgent = text_to_features("紧急危险警报")
        f_calm = text_to_features("平静微风")
        assert f_urgent[5] >= f_calm[5]


class TestNeuron:
    def test_forward_output_in_range(self):
        n = Neuron(0, n_inputs=8, seed=42)
        inputs = [0.5] * 8
        out = n.forward(inputs)
        assert 0.0 <= out <= 1.0

    def test_forward_deterministic(self):
        n = Neuron(0, n_inputs=8, seed=100)
        inputs = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        out1 = n.forward(inputs)
        out2 = n.forward(inputs)
        assert out1 == out2

    def test_different_seeds_different_output(self):
        n1 = Neuron(0, n_inputs=4, seed=1)
        n2 = Neuron(0, n_inputs=4, seed=2)
        inputs = [0.5, 0.5, 0.5, 0.5]
        assert n1.forward(inputs) != n2.forward(inputs)

    def test_process_signal_returns_string(self):
        n = Neuron(1, n_inputs=8, seed=42)
        result = n.process_signal("测试信号")
        assert isinstance(result, str)
        assert "测试信号" in result

    def test_handles_empty_inputs(self):
        n = Neuron(0, n_inputs=8, seed=42)
        out = n.forward([])
        assert 0.0 <= out <= 1.0


class TestNeuralLayer:
    def test_forward_returns_correct_count(self):
        layer = NeuralLayer(n_neurons=4, n_inputs=8, seed=0)
        inputs = [0.5] * 8
        outputs = layer.forward(inputs)
        assert len(outputs) == 4

    def test_all_outputs_in_range(self):
        layer = NeuralLayer(n_neurons=6, n_inputs=8, seed=0)
        inputs = [0.3] * 8
        for v in layer.forward(inputs):
            assert 0.0 <= v <= 1.0


class TestSynapticNetwork:
    def test_forward_returns_output_layer_size(self):
        net = SynapticNetwork([8, 12, 6, 4], base_seed=42)
        inputs = [0.5] * 8
        out = net.forward(inputs)
        assert len(out) == 4

    def test_dominant_index_in_range(self):
        net = SynapticNetwork([8, 12, 6, 4], base_seed=42)
        inputs = [0.5] * 8
        idx = net.dominant_index(inputs)
        assert 0 <= idx <= 3

    def test_activation_strength_in_range(self):
        net = SynapticNetwork([8, 12, 6, 4], base_seed=42)
        inputs = [0.5] * 8
        strength = net.activation_strength(inputs)
        assert 0.0 <= strength <= 1.0

    def test_different_inputs_different_output(self):
        net = SynapticNetwork([8, 12, 6, 4], base_seed=42)
        out1 = net.forward([0.0] * 8)
        out2 = net.forward([1.0] * 8)
        assert out1 != out2

    def test_deterministic(self):
        net = SynapticNetwork([8, 12, 6, 4], base_seed=99)
        inputs = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        assert net.forward(inputs) == net.forward(inputs)

    def test_different_seeds_different_networks(self):
        net1 = SynapticNetwork([8, 4], base_seed=1)
        net2 = SynapticNetwork([8, 4], base_seed=2)
        inputs = [0.5] * 8
        assert net1.forward(inputs) != net2.forward(inputs)

    def test_custom_layer_sizes(self):
        net = SynapticNetwork([8, 16, 8, 4, 2], base_seed=42)
        inputs = [0.5] * 8
        out = net.forward(inputs)
        assert len(out) == 2


class TestGlialCell:
    def test_maintain_environment(self):
        cell = GlialCell()
        result = cell.maintain_environment()
        assert isinstance(result, str)
        assert len(result) > 0


class TestCerebrospinalFluid:
    def test_circulate(self):
        csf = CerebrospinalFluid()
        result = csf.circulate()
        assert isinstance(result, str)
        assert "脑脊液" in result
