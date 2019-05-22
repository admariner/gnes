import os
from typing import List, Tuple

import numpy as np

from .base import BaseBinaryIndexer


class AnnoyIndexer(BaseBinaryIndexer):
    lock_work_dir = True

    def __init__(self, num_dim: int, data_path: str, metric: str = 'angular', n_trees=10, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.num_dim = num_dim
        self.work_dir = data_path
        self.indexer_file_path = os.path.join(self.work_dir, self.internal_index_path)
        self.metric = metric
        self.n_trees = n_trees
        self._doc_ids = []

    def _post_init(self):
        from annoy import AnnoyIndex
        self._index = AnnoyIndex(self.num_dim, self.metric)
        try:
            self._index.load(self.indexer_file_path)
        except:
            self.logger.warning('fail to load model from %s, will init an empty one' % self.indexer_file_path)

    def add(self, keys: List[int], vectors: np.ndarray, *args, **kwargs):
        if len(vectors) != len(keys):
            raise ValueError("vectors length should be equal to doc_ids")

        if vectors.dtype != np.float32:
            raise ValueError("vectors should be ndarray of float32")

        last_idx = len(self._doc_ids)
        for idx, vec in enumerate(vectors):
            self._index.add_item(last_idx + idx, vec)
        self._doc_ids += keys

    def query(self, keys: np.ndarray, top_k: int, *args, **kwargs) -> List[List[Tuple]]:
        self._index.build(self.n_trees)
        if keys.dtype != np.float32:
            raise ValueError("vectors should be ndarray of float32")
        res = []
        for k in keys:
            ret, score = self._index.get_nns_by_vector(k, top_k, include_distances=True)
            res.append([(self._doc_ids[r], -s) for r, s in zip(ret, score)])
        return res

    @property
    def size(self):
        return self._index.get_n_items()

    def __getstate__(self):
        d = super().__getstate__()
        self._index.save(self.indexer_file_path)
        del d['_index']
        return d