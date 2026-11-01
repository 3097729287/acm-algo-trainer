"""Validate complete outputs for tasks with multiple accepted constructions."""
import itertools
from core7_checkers_recurrence import tromino
from core7_checkers_greedy import stack_computer,mex_graph,majority_tree,blackboard,gcd_lcm,equal_permutations


def bitset(inp, got, other=None):
    data=iter(inp.split());tokens=iter(got.split())
    try:
        tests=int(next(data))
        for _ in range(tests):
            n,k=int(next(data)),int(next(data));s=next(data)
            verdict=next(tokens).upper()
            if verdict=='NO':
                if '1'*k not in s:
                    return False, 'NO but there is no forced all-one interval'
                continue
            if verdict!='YES':
                return False,'Unknown verdict'
            p=[int(next(tokens)) for _ in range(n)]
            if sorted(p)!=list(range(1,n+1)):
                return False,'Not a permutation'
            # Inspect every allowed interval rather than the construction rule.
            for left in range(n):
                maximum=left
                for right in range(left,n):
                    if p[right]>p[maximum]:maximum=right
                    if right-left+1>=k and s[maximum]=='1':
                        return False,f'Forbidden maximum on interval {left+1},{right+1}'
        if next(tokens,None) is not None:
            return False,'Extra output'
        return True
    except (ValueError,StopIteration):
        return False,'Missing or malformed output'

from core7_interactive import weighing_transcript,kachina_transcript
from core7_checkers_binary import rooks,sign_route
from core7_checkers_topology import family_order,task_order,ranking_order,blog_order,two_paths_color,directed_edges
from core7_checkers_shortest import path_decimal
from core7_checkers_mst import mst_decimal,shortest_tree
from core7_interactive_mst import railway_transcript
from core7_checkers_trees import tree_embedding,tree_overlap_intervals
from core7_checkers_knapsack import fifo_selection
from core7_checkers_interval import bracket_supersequence
from core7_checkers_tree_dp import critical_fraction
from core7_checkers_subset_dp import reward_fraction

from core7_checkers_fenwick import path_value_verdicts
