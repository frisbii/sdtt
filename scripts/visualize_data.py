import argparse
import itertools
import pandas as pd
from confer import add_config_path, Config, PROJECT_ROOT
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.container import BarContainer
import mplcursors


def show_annotation(sel: mplcursors.Selection):
    if type(sel.artist) == BarContainer:
        bar = sel.artist[sel.index]
        sel.annotation.set_text(f"{sel.artist.get_label()}: {bar.get_height():.3f}")
        sel.annotation.xy = (
            bar.get_x() + bar.get_width() / 2,
            bar.get_y() + bar.get_height() / 2,
        )
        sel.annotation.get_bbox_patch().set_alpha(0.8)


def get_parameter_values(config: Config, parameter_name: str):
    values = getattr(config.visualization, parameter_name + 's')
    if values == []:
        values = getattr(config.generation, parameter_name + 's')
    return values


def generate_plots(config: Config, df: pd.DataFrame):
    # Compute the list of designs to visualize this run.
    designs = list(
        itertools.product(
            *[
                get_parameter_values(config, param)
                for param in config.visualization.parameters_order[:-1]
            ]
        )
    )

    # create figure and prepare subfigures
    fig = plt.figure()
    sfigs = fig.subfigures(1, len(designs), squeeze=False)[0]

    df = df.reset_index().set_index(config.visualization.parameters_order)
    
    # VISUALIZATION
    for i, p in enumerate(designs):
        # Create figure and axes
        subfig = sfigs[i]
        axs = sfigs[i].subplots(3, 1, sharex=True)

        #################
        # SUPER STYLING
        subfig.suptitle("\n".join([str(x) for x in p]) + "ns")
        # If this is the leftmost subfigure, add y-labels
        if i == 0:
            axs[0].set_ylabel("Primitives count")
            axs[1].set_ylabel("Delay (ns)")
            axs[2].set_ylabel("Power usage (W)")
        axs[2].set_xlabel(config.visualization.parameters_order[-1])

        # Utilization
        stack_bars(
            axs[0],
            df.loc[p]
            .drop(
                columns = ["delay_route", "delay_logic", "power_static", "power_dynamic"]
            )
            .copy(),
            config.visualization.categorical
        )
        # Timing
        stack_bars(axs[1], df.loc[p].loc[:, ["delay_route", "delay_logic"]].copy(), config.visualization.categorical)
        # Power
        stack_bars(axs[2], df.loc[p].loc[:, ["power_dynamic"]].copy(), config.visualization.categorical)

    if config.visualization.show_annotation:
        cursor = mplcursors.cursor(hover=True)
        cursor.connect("add", show_annotation)
        
    plt.show()


def stack_bars(ax: Axes, df: pd.DataFrame, is_categorical: bool):
    bottom_values = [0] * len(df)
    xtick_locations = range(len(df.index)) if is_categorical else df.index
    for col in df.columns:
        # plot each column on top of each other
        ax.bar(xtick_locations, df[col], bottom=bottom_values, label=col, width=0.95 if is_categorical else 1)
        ax.set_xticks(xtick_locations, df.index)
        # add the new values to the bottom_values baseline to prepare for the next column
        bottom_values = [i + j for i, j in zip(bottom_values, df[col])]
    ax.legend()


def main():
    global df
    ####################
    # ARGUMENT PARSING
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        default="data.hdf",
        help="specify a filename for the input hdf (default: /data.hdf)",
        metavar="file",
    )
    add_config_path(parser)
    args = parser.parse_args()
    infile = args.f
    config = Config(args.config_path)
    ####################

    ####################
    # PLOT STYLING
    # Set seaborn matplotlib theme
    sns.set_theme()
    sns.set_context(rc={"patch.linewidth": 0.0})
    # Set legend size to x-small for space
    plt.rc("legend", fontsize="x-small")
    ####################

    # Load dataframe
    df = pd.read_hdf(PROJECT_ROOT / infile, key="df")
    # Generates comparison plots for specified parameters
    generate_plots(config, df)


if __name__ == "__main__":
    main()
