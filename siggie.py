# Siggie - Feature Hashing for Labeled Graphs
# (c) 2015 Konrad Rieck (konrad@mlsec.org)

import sys
from collections import defaultdict

import networkx as nx

import utils


# Supported modes for bags
modes = {
    0: "bag_of_nodes",
    1: "bag_of_edges",
    2: "bag_of_weakly_connected_components",
    3: "bag_of_strongly_connected_components",
    4: "bag_of_attracting_components",
    5: "bag_of_neighborhoods",
    6: "bag_of_reachabilities",
    7: "bag_of_shortest_paths"
}

def mode_name(mode, args):
    """ Return the name and config of a bag mode """

    s = modes[mode].replace("_", " ")
    if mode == 5:
        s += " (size: %d)" % args.size
    elif mode == 6:
        s += " (depth: %d)" % args.depth
    elif mode == 7:
        s += " (maxlen: %d)" % args.maxlen
    return s


def bag_of_nodes(graph, args):
    """ Build bag of nodes from graph """

    bag = {}
    for i in graph.nodes():
        label = graph.node[i]["label"]
        if label not in bag:
            bag[label] = 0
        bag[label] += 1

    return bag


def bag_of_edges(graph, args):
    """ Build bag of edges from graph """

    bag = {}
    for i, j in graph.edges():
        label = "%s-%s" % (graph.node[i]["label"], graph.node[j]["label"])
        if label not in bag:
            bag[label] = 0
        bag[label] += 1

    return bag


def bag_of_neighborhoods(graph, args):
    """ Build bag of neighborhoods for graph """

    paths = nx.all_pairs_shortest_path(graph, cutoff=args.size)

    bag = {}
    for i in paths:
        reachable = paths[i].keys()
        if len(reachable) == 0:
            continue

        ns = map(lambda x: graph.node[x]["label"], reachable)
        label = "%s:%s" % (graph.node[i]["label"], '-'.join(sorted(ns)))

        if label not in bag:
            bag[label] = 0.0
        bag[label] += 1.0

    return bag


def bag_of_reachabilities(graph, args):
    """ Build bag of reachabilities for graph """

    paths = nx.all_pairs_shortest_path(graph, cutoff=args.depth)

    bag = {}
    for i in paths:
        reachable = paths[i].keys()
        if len(reachable) == 0:
            continue

        for j in reachable:
            label = "%s:%s" % (
                graph.node[i]["label"], graph.node[j]["label"]
            )

            if label not in bag:
                bag[label] = 0.0
            bag[label] += 1.0

    return bag


def bag_of_shortest_paths(graph, args):
    """ Build bag of shortest path for graph """

    paths = nx.all_pairs_shortest_path(graph, cutoff=args.maxlen)

    bag = {}
    for i in paths:
        for j in paths[i]:
            path = map(lambda x: graph.node[x]["label"], paths[i][j])
            label = '-'.join(path)
            if label not in bag:
                bag[label] = 0.0
            bag[label] += 1.0

    return bag


def bag_of_strongly_connected_components(graph, args):
    """ Bag of strongly connected components """
    comp = nx.strongly_connected_components(graph)
    return bag_of_components(graph, comp)


def bag_of_weakly_connected_components(graph, args):
    """ Bag of weakly connected components """
    comp = nx.weakly_connected_components(graph)
    return bag_of_components(graph, comp)


def bag_of_biconnected_components(graph, args):
    """ Bag of bi-connected components """
    comp = nx.biconnected_components(graph)
    return bag_of_components(graph, comp)


def bag_of_attracting_components(graph, args):
    """ Bag of attracting components """
    comp = nx.attracting_components(graph)
    return bag_of_components(graph, comp)


def bag_of_components(graph, comp):
    """ Build bag of components for graph """

    bag = {}
    for nodes in comp:
        ns = map(lambda x: graph.node[x]["label"], nodes)
        label = '-'.join(sorted(ns))
        if label not in bag:
            bag[label] = 0
        bag[label] += 1

    return bag


def bag_to_fvec(bag, bits=24, fmap=None):
    """ Map bag to sparse feature vector """

    fvec = {}
    hashes = {}

    for key in bag:
        hash = utils.murmur3(key)
        dim = hash & (1 << bits) - 1
        sign = 2 * (hash >> 31) - 1

        if dim not in fvec:
            fvec[dim] = 0
        fvec[dim] += sign * bag[key]

        # Store dim-key mapping
        if fmap:
            if dim not in hashes:
                hashes[dim] = set()
            if key not in hashes[dim]:
                hashes[dim].add(key)

    return fvec, hashes if fmap else None
