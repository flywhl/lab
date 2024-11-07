from rich import print
from rich.panel import Panel

import termplotlib as tpl
import numpy


def test_plot():
    x = numpy.linspace(0, 2 * numpy.pi, 10)
    y = numpy.sin(x)

    fig = tpl.figure()
    fig.plot(x, y, label="data", width=100, height=30)

    # print(Panel(fig.get_string(), title="myplot"))
    print(fig.get_string())
