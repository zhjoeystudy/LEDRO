import numpy as np
import sys
from copy import deepcopy, copy


class Design(list):
    """
    Represents a single design point in the search space.

    It inherits from 'list' and its contents are the indices of the parameters
    for this specific design.
    """

    def __init__(self, spec_range, seq=()):
        """
        Initializes a Design.

        :param spec_range: Dict[Str: List[float, float]] defining the valid range for each spec.
        :param seq: A sequence of parameter indices that define this design.
        """
        list.__init__(self, seq)
        self.__cost = None
        self.__fitness = None
        self.specs = {spec_kwrd: None for spec_kwrd in spec_range.keys()}

        # The ID is now generated directly and stored as a simple attribute.
        self.id = '_'.join(map(str, seq))

        self.spec_range = spec_range
        self.parent1 = None
        self.parent2 = None
        self.sibling = None

    def set_parents_and_sibling(self, parent1, parent2, sibling):
        self.parent1 = parent1
        self.parent2 = parent2
        self.sibling = sibling

    def is_init_population(self):
        return self.parent1 is None

    def is_mutated(self):
        return self.parent1 is not None and self.parent2 is None

    @property
    def cost(self):
        return self.__cost

    @property
    def fitness(self):
        return self.__fitness

    @cost.setter
    def cost(self, x):
        self.__cost = x
        self.__fitness = -x if x is not None else None

    @fitness.setter
    def fitness(self, x):
        self.__fitness = x
        self.__cost = -x if x is not None else None

    @staticmethod
    def recreate_design(spec_range, old_design):
        """
        Creates a new Design object from an existing one.
        The 'eval_core' argument is no longer needed.
        """
        # The sequence for the new design is the old_design itself (since it's a list)
        dsn = Design(spec_range, old_design)
        dsn.specs.update(**old_design.specs)
        for attr in dsn.__dict__.keys():
            if (attr in old_design.__dict__.keys()) and (attr not in ['specs']):
                dsn.__dict__[attr] = deepcopy(old_design.__dict__[attr])
        return dsn

    @staticmethod
    def genocide(*args):
        """Resets the lineage of one or more designs."""
        for dsn in args:
            dsn.parent1 = None
            dsn.parent2 = None
            dsn.sibling = None

    def copy(self):
        """Creates a shallow copy of the design list and a deep copy of the specs."""
        new = copy(self)
        new.specs = deepcopy(self.specs)
        return new