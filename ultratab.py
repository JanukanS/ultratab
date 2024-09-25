from dataclasses import dataclass
from functools import cached_property, partialmethod
import ipywidgets as widgets
from inspect import signature
from itertools import product

@dataclass
class TabView:
    tabDict: dict

    @cached_property
    def TabChildren(self):
        outList = []
        for _, tbFunc in self.tabDict.items():
            outList.append(widgets.Output())
            with outList[-1]:
                if type(tbFunc) == dict:
                    display(TabView(tbFunc).Tab)
                else:
                    tbFunc()
        return outList

    @cached_property
    def Tab(self):
        tb = widgets.Tab()
        tb.children = self.TabChildren
        tab_titles = list(self.tabDict.keys())
        for ind, tt in enumerate(tab_titles):
            tb.set_title(ind, tt)
        return tb

class InteractivePlotGen:

    @classmethod
    def extractSliders(cls, genObj, genPlotFunc):
        """get the sliders required for the interactive widget"""
        argCont = genPlotFunc.__code__.co_argcount
        argList = genPlotFunc.__code__.co_varnames[1:argCont]
        return {argName: getattr(genObj, argName) for argName in argList}


    @classmethod
    def plotMethod(cls, genObj, genPlotFunc):
        """Create and display an interactive widget based on an object method"""
        sliders = cls.extractSliders(genObj, genPlotFunc)
        opw = widgets.Output()
        def plotFunc(**kwargs):
            opw.clear_output()
            with opw:
                genPlotFunc(**kwargs)

        intWidget = widgets.interactive(plotFunc, {"manual": True},**sliders)
        combWidgets = widgets.VBox([intWidget, opw])
        display(combWidgets)


class TabGen:
    _plot_prefix = "plot_"
    _genplot_prefix = "genPlot_"

    @classmethod
    def _extract_plot_methods(cls, obj):
        plotAttrs = [val for val in dir(obj) if val.startswith(cls._plot_prefix)]
        methodLocFunc = lambda methodName: getattr(type(obj), methodName).__code__.co_firstlineno
        plotAttrs.sort(key=methodLocFunc)
        plotNames = [val[len(cls._plot_prefix):] for val in plotAttrs]
        return {nameVal: getattr(obj, attrVal) for nameVal, attrVal in zip(plotNames, plotAttrs)}

    @classmethod
    def _extract_genplot_methods(cls, obj):
        genPlotAttrs = [val for val in dir(obj) if val.startswith(cls._genplot_prefix)]
        methodLocFunc = lambda methodName: getattr(type(obj), methodName).__code__.co_firstlineno
        genPlotAttrs.sort(key=methodLocFunc)
        genPlotNames = [val[len(cls._genplot_prefix):] for val in genPlotAttrs]
        funcGen = lambda obj, attrName: lambda: InteractivePlotGen.plotMethod(obj, getattr(obj, attrName))
        return {nameVal: funcGen(obj, attrVal) for nameVal, attrVal in zip(genPlotNames, genPlotAttrs)}

    @classmethod
    def extractDict(cls, obj):
        plotPair = cls._extract_plot_methods(obj)
        plotPair.update(cls._extract_genplot_methods(obj))
        return plotPair

    @classmethod
    def generate(cls, objDict: dict):
        tabDict = {key: cls.extractDict(val) for key, val in objDict.items()}
        return TabView(tabDict)

    @classmethod
    def plot(cls, objDict: dict):
        TabObj = cls.generate(objDict)
        display(TabObj.Tab)
