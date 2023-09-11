import copy
from collections import deque
from twolayerindex import Bitmap
import hashlib
import math

class FilterNode:
    def __init__(self, q, range_start, range_end):
        self.q = q
        self.bitmap = None
        self.hash_value = None
        self.left_child = None
        self.middle_child = None
        self.right_child = None
        self.range_start = range_start
        self.range_end = range_end
        self.r = range(range_start, range_end)
        self.parent_node = None

    def compute_hash(self):
        if self.left_child.is_leaf_node() and self.middle_child.is_leaf_node() and self.right_child.is_leaf_node():

            content = str(self.left_child.r) + self.left_child.bitmap.show_bitmap() + str(
                self.middle_child.r) + self.middle_child.bitmap.show_bitmap() + str(
                self.right_child.r) + self.right_child.bitmap.show_bitmap()

        else:
            if self.left_child.is_leaf_node() and self.middle_child.is_leaf_node() and not self.right_child.is_leaf_node():
                content = str(self.left_child.r) + self.left_child.bitmap.show_bitmap() + str(
                    self.middle_child.r) + self.middle_child.bitmap.show_bitmap() + str(
                    self.right_child.r) + self.right_child.hash_value
            elif self.left_child.is_leaf_node() and not self.middle_child.is_leaf_node() and self.right_child.is_leaf_node():
                content = str(self.left_child.r) + self.left_child.bitmap.show_bitmap() + str(
                    self.middle_child.r) + self.middle_child.hash_value + str(
                    self.right_child.r) + self.right_child.bitmap.show_bitmap()
            elif not self.left_child.is_leaf_node() and self.middle_child.is_leaf_node() and self.right_child.is_leaf_node():
                content = str(self.left_child.r) + self.left_child.hash_value + str(
                    self.middle_child.r) + self.middle_child.bitmap.show_bitmap() + str(
                    self.right_child.r) + self.right_child.bitmap.show_bitmap()
            else:

                content = str(self.left_child.r) + self.left_child.hash_value + str(
                    self.middle_child.r) + self.middle_child.hash_value + str(
                    self.right_child.r) + self.right_child.hash_value

        self.hash_value = hashlib.sha256(content.encode('utf-8')).hexdigest()

    def is_leaf_node(self):
        return self.bitmap is not None


class FilterLayer:
    def __init__(self, q, min_val, max_val, num_buckets):
        self.q = q
        self.min_val = min_val
        self.max_val = max_val
        self.num_buckets = num_buckets
        self.bucket_size = math.ceil((max_val - min_val) // num_buckets)
        self.root_node = self.build_index_tree(q, self.min_val, self.max_val)
        self.root_hash = self.root_node.hash_value

    def build_index_tree(self, q, range_start, range_end):
        node = FilterNode(q, range_start, range_end)

        if range_end - range_start > self.bucket_size:
            # Non-leaf node creation
            m_1 = math.ceil(range_start + (range_end - range_start) // 3)
            m_2 = math.ceil(range_start + (range_end - range_start) // 3 * 2)
            left_child = self.build_index_tree(q, range_start, m_1)
            left_child.parent_node = node
            middle_child = self.build_index_tree(q, m_1, m_2)
            middle_child.parent_node = node
            right_child = self.build_index_tree(q, m_2, range_end)
            right_child.parent_node = node

            node.left_child = left_child
            node.middle_child = middle_child
            node.right_child = right_child

            node.compute_hash()
        else:
            node.bitmap = Bitmap.Bitmap(q)

        return node

    id_array_temp = []

    digest_array_temp = []

    def insert(self, idn, value):  # 前q个区块插入
        leaf_node = self.find_leaf_node(self.root_node, value)
        leaf_node.bitmap.set_bit(idn, 1)
        n = leaf_node.parent_node
        while n is not None:
            n.compute_hash()
            n = n.parent_node

        self.id_array_temp.append(idn)
        self.digest_array_temp.append(value)
        return leaf_node

    def update(self, new_id, new_value):  # q+1个区块开始更新
        old_value = self.digest_array_temp.pop(0)
        i = new_id % self.q
        old_leaf_node = self.find_leaf_node(self.root_node, old_value)
        old_leaf_node.bitmap.set_bit(i, 0)
        n = old_leaf_node.parent_node
        while n is not None:
            n.compute_hash()
            n = n.parent_node
        new_leaf_node = self.find_leaf_node(self.root_node, new_value)
        new_leaf_node.bitmap.set_bit(i, 1)
        n1 = new_leaf_node.parent_node
        while n1 is not None:
            n1.compute_hash()
            n1 = n1.parent_node

        self.id_array_temp[i] = new_id
        return new_leaf_node

    def find_leaf_node(self, node, value):
        if node.is_leaf_node():
            return node
        elif value < node.range_start + (node.range_end - node.range_start) // 3:
            return self.find_leaf_node(node.left_child, value)
        elif value >= node.range_start + (node.range_end - node.range_start) // 3 * 2:
            return self.find_leaf_node(node.right_child, value)
        else:
            return self.find_leaf_node(node.middle_child, value)

    def range_query(self, id_set, query_start, query_end):

        return self._range_query(self.root_node, id_set, query_start, query_end)

    result = deque()
    reinforce_need_range = deque()
    vo_1 = []
    len_result = deque()

    def _range_query(self, node, id_set, query_start, query_end):
        if node.is_leaf_node():
            if node.range_end < query_start or node.range_start > query_end:
                pass
            else:
                indexes = deque()

                for ids in id_set:
                    i = ids % self.q
                    if node.bitmap.check_bit(i):
                        indexes.append(ids)
                if len(indexes) != 0:
                    self.result.extend(indexes)
                    self.len_result.append(len(indexes))
                    self.reinforce_need_range.append(node.range_start)
                    self.reinforce_need_range.append(node.range_end)

        else:
            if node.range_end < query_start or node.range_start > query_end:
                pass
            else:
                self._range_query(node.left_child, id_set, query_start, query_end)
                self._range_query(node.middle_child, id_set, query_start, query_end)
                self._range_query(node.right_child, id_set, query_start, query_end)
        return self.result

    def vo_construct(self, id_set, query_start, query_end):

        return self._vo_construct(self.root_node, id_set, query_start, query_end)

    def _vo_construct(self, node, id_set, query_start, query_end):
        if node.is_leaf_node():
            if node.range_end < query_start or node.range_start > query_end:
                # Pruned node
                self.vo_1.append(node.r)
                self.vo_1.append(node.bitmap)

            else:
                # Leaf node
                self.vo_1.append(node.r)
                self.vo_1.append(node.bitmap)

        else:
            if node.range_end < query_start or node.range_start > query_end:
                # Pruned node
                self.vo_1.append(node.r)
                self.vo_1.append(node.hash_value)
            else:
                # Non-leaf node
                self.vo_1.append('[')
                self._vo_construct(node.left_child, id_set, query_start, query_end)
                self._vo_construct(node.middle_child, id_set, query_start, query_end)
                self._vo_construct(node.right_child, id_set, query_start, query_end)
                self.vo_1.append(']')
        return self.vo_1

    def hash_root(self, vo_1):
        r, h = self._hash_root(vo_1)
        return h[-64:]

    def _hash_root(self, vo_1):
        s = ""  # 用于保存字符串
        r = range(0)
        while vo_1:
            e = vo_1.pop(0)  # 从 VO 中取出下一个 entry
            if type(e) is range:
                e1 = vo_1.pop(0)
                if type(e1) is Bitmap.Bitmap:
                    s += str(e) + e1.show_bitmap()
                    s1 = set(r)
                    s2 = set(e)
                    union_set = s1.union(s2)
                    result_range = range(min(union_set), max(union_set) + 1)
                    r = result_range
                else:
                    s += str(e) + e1
                    s1 = set(r)
                    s2 = set(e)
                    union_set = s1.union(s2)
                    result_range = range(min(union_set), max(union_set) + 1)
                    r = result_range
            elif e == "[":
                ra, h = self._hash_root(vo_1)  # 递归调用 RootHash
                s += str(ra) + h
                s1 = set(r)
                s2 = set(ra)

                union_set = s1.union(s2)

                result_range = range(min(union_set), max(union_set) + 1)
                r = result_range

            elif e == "]":
                return r, hashlib.sha256(s.encode("utf-8")).hexdigest()
        return r, s


class ReinforcementLayer:
    def __init__(self, q, p, min_value, max_value, num_buckets):
        self.reinforce_layer_bitmap = []
        self.filter_layer = FilterLayer(q, min_value, max_value, num_buckets)
        self.filter_layer_root_node = self.filter_layer.root_node
        self.p = p
        self.q = q
        self.hash_fr_root = None
        self.flag = [0] * self.p
        self.single_flag = [0] * self.p
        self.build_bitmap()

    def build_bitmap(self):

        for r in range(self.p):
            g = Bitmap.Bitmap(self.q)
            self.reinforce_layer_bitmap.append(g)
        self.compute_hash()

    def compute_hash(self):
        content = ''
        for j in range(self.p):
            content += hashlib.sha256(str(self.reinforce_layer_bitmap[j].show_bitmap()).encode('utf-8')).hexdigest()
        self.hash_fr_root = hashlib.sha256(content.encode('utf-8')).hexdigest()

    def set_bitmap_bit(self, value, loc, min_val, max_val, y):

        middle = math.ceil((min_val + max_val) / 2)
        if value < middle:
            self.reinforce_layer_bitmap[y].set_bit(loc, 0)
            if y < self.p - 1:
                self.set_bitmap_bit(value, loc, min_val, middle, y + 1)
        else:
            self.reinforce_layer_bitmap[y].set_bit(loc, 1)
            if y < self.p - 1:
                self.set_bitmap_bit(value, loc, middle, max_val, y + 1)

    def insert(self, value, idn):  # 前q个
        value_loc_node = self.filter_layer.insert(idn, value)
        self.set_bitmap_bit(value, idn, value_loc_node.range_start, value_loc_node.range_end, 0)
        self.compute_hash()

    def update(self, value, new_id):  # q+1个开始
        i = new_id % self.q
        value_loc_node = self.filter_layer.update(new_id, value)
        self.set_bitmap_bit(value, i, value_loc_node.range_start, value_loc_node.range_end, 0)
        self.compute_hash()

    vo_1 = None
    vo_2 = []
    range_index = 0
    range_indexes_to_remove = []

    def range_query(self, id_set, query_start, query_end):

        range_index = 0
        self.filter_layer.range_query(id_set, query_start, query_end)
        value_loc_range = self.filter_layer.reinforce_need_range

        self.final_result = list(self.filter_layer.result)
        bitmap = self.reinforce_layer_bitmap

        while value_loc_range:
            min_range = value_loc_range.popleft()
            max_range = value_loc_range.popleft()
            num = self.filter_layer.len_result.popleft()
            cnt = 0
            while cnt < num:
                cnt += 1

                result_id = self.filter_layer.result.popleft()

                self.sub_range_query(query_start, query_end, min_range, max_range, result_id, 0, bitmap, range_index,
                                     self.flag)
                range_index += 1

        # 按照索引逆序排序，这样删除元素时不会影响后续元素的索引
        self.range_indexes_to_remove.sort(reverse=True)
        # 逐个删除元素
        for index in self.range_indexes_to_remove:
            del self.final_result[index]
        self.range_indexes_to_remove.clear()

    final_result = []

    def sub_range_query(self, query_start, query_end, min_range, max_range, result_id, y, bitmap, index, flag):
        mid = (min_range + max_range) // 2
        i = result_id % self.q
        if bitmap[y].check_bit(i):
            if max_range < query_start or mid > query_end:
                self.range_indexes_to_remove.append(index)
                flag[y] = 1
            elif query_start <= mid and query_end >= max_range:
                flag[y] = 1
            else:
                flag[y] = 1
                if y < self.p - 1:
                    self.sub_range_query(query_start, query_end, mid, max_range, result_id, y + 1, bitmap, index, flag)
        elif not bitmap[y].check_bit(i):
            if mid < query_start or min_range > query_end:
                self.range_indexes_to_remove.append(index)
                flag[y] = 1
            elif query_start <= min_range and query_end >= mid:
                flag[y] = 1
            else:
                flag[y] = 1
                if y < self.p - 1:
                    self.sub_range_query(query_start, query_end, min_range, mid, result_id, y + 1, bitmap, index, flag)

    def vo_construct(self, id_set, query_start, query_end):
        self.filter_layer.vo_construct(id_set, query_start, query_end)
        self.vo_1 = self.filter_layer.vo_1
        for t in range(self.p):
            a = self.reinforce_layer_bitmap[t]

            if self.flag[t] == 1:

                self.vo_2.append(a)
            else:
                self.vo_2.append(hashlib.sha256(a.show_bitmap().encode('utf-8')).hexdigest())

    def re_construct_fr_root(self, vo_2):
        s_r1 = ''
        while vo_2:
            e = vo_2.pop(0)
            if type(e) is Bitmap.Bitmap:
                s_r1 += hashlib.sha256(e.show_bitmap().encode('utf-8')).hexdigest()
            else:
                s_r1 += e
        fr_root = hashlib.sha256(s_r1.encode('utf-8')).hexdigest()
        return fr_root


    def verify_digest_value(self, vo_1, vo_2):
        fi_root = self.filter_layer.root_node.hash_value
        fr_root = self.hash_fr_root
        fi_root_re = self.filter_layer.hash_root(vo_1)
        fr_root_re = self.re_construct_fr_root(vo_2)
        return self._verify_digest_value(fi_root, fr_root, fi_root_re, fr_root_re)

    def _verify_digest_value(self, fi_chain, fr_chain, fi_re, fr_re):
        if fi_chain == fi_re and fr_chain == fr_re:
            return True
        return False

    def filter_node_bfs(self):
        node = [self.filter_layer.root_node]
        filter_node = []
        while node:
            n = node.pop()
            filter_node.append(n)
            if n.left_child and n.right_child:
                node.append(n.left_child)
                node.append(n.right_child)
        return filter_node

    def filter_node_content(self):
        node = [self.filter_layer.root_node]
        filter_node_content = []
        while node:
            n = node.pop(0)
            filter_node_content.append(n.r)
            if n.left_child and n.right_child:
                node.append(n.left_child)
                node.append(n.middle_child)
                node.append(n.right_child)
            if n.left_child and n.right_child:
                filter_node_content.append(n.hash_value)
            else:
                filter_node_content.append(n.bitmap)

        return filter_node_content

    def reinforce_content(self):
        bitmap = []
        for i in self.reinforce_layer_bitmap:
            bitmap.append(i.show_bitmap())
        return bitmap

