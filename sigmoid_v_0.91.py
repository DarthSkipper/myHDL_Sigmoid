""" Biblioteka sigmoid by Marek K. & Michał M.

"""
from myhdl import instance, ResetSignal, delay, StopSimulation, always, block, always_seq, Signal, intbv, enum, always_comb, instances
from clk_gen import clk_gen
import os
from axis import Axis


# -----------------------------------------------------
# Power's block
# -----------------------------------------------------
@block
def power(t_clk, t_reset, t_y_out, t_base, t_power, t_end, t_start):
    """

    :param t_clk:   clock
    :param t_reset: reset
    :param t_y_out: output
    :param t_base:
    :param t_power:
    :param t_end:
    :param t_start:
    :return:
    """
    state_t = enum('count', 'result')
    state = Signal(state_t.count)
    accumulator = Signal(intbv(1)[32:])
    counter = Signal(intbv(0)[32:])

    @always_seq(t_clk.posedge, reset=t_reset)
    def powers():
        """

        :return:
        """
        if state == state_t.count:
            if t_start == 1:
                t_end.next = 0
                accumulator.next = accumulator * t_base
                counter.next = counter + 1
                if counter >= t_power-1:
                    state.next = state_t.result
                    counter.next = 0
        elif state == state_t.result:
            t_end.next = 1
            t_y_out.next = accumulator
            accumulator.next = 1
            state.next = state_t.count
        else:
            raise ValueError("Undefined state")

    return instances()


# -----------------------------------------------------
# Factorial's block
# -----------------------------------------------------
@block
def factorial(t_clk, t_reset, t_y_out, t_factorial, t_end, t_start):
    """

    :param t_clk:
    :param t_reset:
    :param t_y_out:
    :param t_factorial:
    :param t_end:
    :param t_start:
    :return:
    """
    state_t = enum('count', 'result')
    state = Signal(state_t.count)
    accumulator = Signal(intbv(1)[32:])
    counter = Signal(intbv(0)[32:])

    @always_seq(t_clk.posedge, reset=t_reset)
    def factorials():
        if state == state_t.count:
            if t_start == 1:
                t_end.next = 0
                if counter == 0:
                    counter.next = 1
                    accumulator.next = 1
                else:
                    accumulator.next = accumulator * counter
                    counter.next = counter + 1
                if counter > t_factorial-1:
                    state.next = state_t.result
                    counter.next = 0
        elif state == state_t.result:
            t_end.next = 1
            t_y_out.next = accumulator
            accumulator.next = 1
            state.next = state_t.count
        else:
            raise ValueError("Undefined state")

    return instances()


# -----------------------------------------------------
# Exponential's block
# -----------------------------------------------------
@block
def exponential(t_clk, t_reset, t_y_out, t_x, t_end, t_start, t_prec=4, fraction=16):
    """

    :param t_clk:
    :param t_reset:
    :param t_y_out:
    :param t_x:
    :param t_prec:
    :param t_end:
    :param t_start:
    :return:
    """
    const_1 = Signal(intbv(65536)[32:])
    state_t = enum('count', 'result')
    state = Signal(state_t.count)
    accumulator = Signal(intbv(0)[32:])
    y_pow = Signal(intbv(0)[32:])
    counter = Signal(intbv(0)[32:])
    y_fac = Signal(intbv(1)[32:])
    t_pow_end, t_fac_end = [Signal(intbv(0)[32:]) for i in range(2)]
    t_pow_start, t_fac_start = [Signal(intbv(1)[32:]) for i in range(2)]
    power_1 = power(t_clk, t_reset, y_pow, t_x, counter, t_pow_end, t_pow_start)
    factorial_1 = factorial(t_clk, t_reset, y_fac, counter, t_fac_end, t_fac_start)

    @always_seq(t_clk.posedge, reset=t_reset)
    def exponentials():
        """

        :return:
        """
        if state == state_t.count:
            if t_start == 1:
                t_end.next = 0
                if t_pow_end == 1 and t_fac_end == 1:
                    t_pow_start.next = 0
                    t_fac_start.next = 0
                    if counter == 0:
                        counter.next = 1
                        accumulator.next = const_1
                    else:
                        accumulator.next = accumulator + ((y_pow << fraction) << fraction) // (y_fac << fraction)
                        counter.next = counter + 1
                    if counter > t_prec-1:
                        state.next = state_t.result
                        counter.next = 0
                    t_pow_start.next = 1
                    t_fac_start.next = 1
        elif state == state_t.result:
            t_pow_start.next = 1
            t_fac_start.next = 1
            t_end.next = 1
            t_y_out.next = accumulator
            accumulator.next = const_1
            state.next = state_t.count
        else:
            raise ValueError("Undefined state")

    return instances()

# -----------------------------------------------------
# Sigmoid's block
# -----------------------------------------------------
@block
def sigmoid(t_clk, t_reset, t_y_out, t_x, t_prec=4, fraction=16):
    """

    :param x:
    :param prec:
    :return:
    """
    const_1 = Signal(intbv(65536)[32:])
    state_t = enum('count', 'result')
    state = Signal(state_t.count)
    accumulator = Signal(intbv(0)[32:])
    counter = Signal(intbv(0)[32:])
    t_exp_out, t_exp_end = [Signal(intbv(0)[32:]) for i in range(2)]
    t_exp_start = Signal(intbv(1)[32:])
    exponential_1 = exponential(t_clk, t_reset, t_exp_out, t_x.tdata, t_exp_end, t_exp_start, t_prec, fraction)

    @always_seq(t_clk.posedge, reset=t_reset)
    def sigmoids():
        """

        :return:
        """
        if state == state_t.count:
            if t_exp_end == 1:
                t_exp_start.next = 0
                accumulator.next = ((t_exp_out << fraction) // (t_exp_out + const_1))
                state.next = state_t.result
        elif state == state_t.result:
            t_exp_start.next = 1
            t_y_out.tdata.next = accumulator
            state.next = state_t.count
        else:
            raise ValueError("Undefined state")

    return instances()

# -----------------------------------------------------
# Testbench
# -----------------------------------------------------
@block
def test_sig(vhdl_output_path=None):

    axis_y = Axis(32)
    axis_x = Axis(32)
    y_pow, y_fac, y_exp = [Signal(intbv(0)[32:]) for i in range(3)]
    clk = Signal(bool(0))
    clk_gen_1 = clk_gen(clk, period=10)
    reset = ResetSignal(0, active=1, async=False)
    # power_1 = power(clk, reset, y_pow, x, prec, end, start)
    # factorial_1 = factorial(clk, reset, y_fac, prec, end, start)
    # exponential_1 = exponential(clk, reset, y_exp, x, prec, end, start)
    sigmoid_1 = sigmoid(clk, reset, axis_y, axis_x, 4, fraction=16)

    @instance
    def reset_gen():
        reset.next = 0
        yield delay(4000)
        yield clk.negedge
        reset.next = 1


    @instance
    def stimulus():
        axis_x.tdata.next = 0
        yield delay(1000)
        print("sig z", axis_x.tdata, "o prec 4 =", axis_y.tdata)
        axis_x.tdata.next = 2
        yield delay(1500)
        print("sig z", axis_x.tdata, "o prec 4 =", axis_y.tdata)
        axis_x.tdata.next = 8
        yield delay(1500)
        print("sig z", axis_x.tdata, "o prec 4 =", axis_y.tdata)
        raise StopSimulation()

    if vhdl_output_path is not None:
        sigmoid_1.convert(hdl='VHDL', path=vhdl_output_path)

    return instances()


if __name__ == '__main__':
    trace_save_path = '../out/testbench/'
    vhdl_output_path = '../out/vhdl/'
    os.makedirs(os.path.dirname(trace_save_path), exist_ok=True)
    os.makedirs(os.path.dirname(vhdl_output_path), exist_ok=True)

    tb = test_sig(vhdl_output_path)
    # tb = test_sig()
    tb.config_sim(trace=True, directory=trace_save_path, name='sigmoid_tb')
    tb.run_sim()
