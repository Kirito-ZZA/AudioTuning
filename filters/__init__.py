"""Configurable audio algorithm plugins."""

from filters.base import AudioAlgorithm, ParameterSpec
from filters.registry import AlgorithmChain

__all__ = ["AudioAlgorithm", "ParameterSpec", "AlgorithmChain"]
