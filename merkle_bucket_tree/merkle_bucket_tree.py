import hashlib
import math


class FilterNode:
    def __init__(self, range_start, range_end):
        self.value = None
        self.id = []
        self.hash_value = None
        self.left_child = None
        self.middle_child = None
        self.right_child = None
        self.range_start = range_start
        self.range_end = range_end
        self.r = range(range_start, range_end)
        self.parent_node = None
        self.value_hash = []
        self.segmentation = None

    def compute_hash(self):
        if self.is_leaf_node():
            num = len(self.value) // self.segmentation
            grouped_data = []
            group = []
            for item in self.value_hash:
                group.append(item)
                if len(group) == num:
                    grouped_data.append(group)
                    group = []
            # 处理最后一组元素不足3个的情况
            if len(group) > 0:
                grouped_data.append(group)
            content = ''

            for i in grouped_data:
                temp = ''
                for j in i:
                    temp += j

                content += hashlib.sha256(temp.encode('utf-8')).hexdigest()
        else:
            content = str(self.left_child.r) + self.left_child.hash_value + str(
                self.middle_child.r) + self.middle_child.hash_value + str(
                self.right_child.r) + self.right_child.hash_value

        self.hash_value = hashlib.sha256(content.encode('utf-8')).hexdigest()

    def is_leaf_node(self):
        if self.value is not None:
            return True
        else:
            return False


class BucketTree:
    def __init__(self, min_val, max_val, num_buckets, segmentation):
        self.min_val = min_val
        self.max_val = max_val
        self.segmentation = segmentation
        self.num_buckets = num_buckets
        self.bucket_size = math.ceil((max_val - min_val) / num_buckets)
        self.root_node = self.build_index_tree(segmentation, self.min_val, self.max_val)
        self.root_hash = self.root_node.hash_value

    def build_index_tree(self, segmentation, range_start, range_end):
        node = FilterNode(range_start, range_end)

        if range_end - range_start > self.bucket_size:
            m_1 = math.ceil(range_start + (range_end - range_start) // 3)
            m_2 = math.ceil(range_start + (range_end - range_start) // 3 * 2)
            left_child = self.build_index_tree(segmentation, range_start, m_1)
            left_child.parent_node = node
            middle_child = self.build_index_tree(segmentation, m_1, m_2)
            middle_child.parent_node = node
            right_child = self.build_index_tree(segmentation, m_2, range_end)
            right_child.parent_node = node

            node.left_child = left_child
            node.middle_child = middle_child
            node.right_child = right_child
            node.compute_hash()
        else:
            node.value = []
            node.segmentation = segmentation
            node.compute_hash()
        return node

    id_array_temp = []
    digest_array_temp = []

    def insert(self, idn, value):  # 前q个区块插入
        leaf_node = self.find_leaf_node(self.root_node, value)
        leaf_node.value.append(value)
        leaf_node.id.append(idn)
        hash_of_data = hashlib.sha256(idn.encode('utf-8')).hexdigest()
        leaf_node.value_hash.append(hash_of_data)

        combined = zip(leaf_node.value, leaf_node.id, leaf_node.value_hash)
        sorted_tuples = self.merge_sort_tuples(list(combined))
        value_s, id_s, hash_s = zip(*sorted_tuples)
        leaf_node.value = list(value_s)
        leaf_node.id = list(id_s)
        leaf_node.value_hash = list(hash_s)

        n = leaf_node
        while n is not None:
            n.compute_hash()
            n = n.parent_node

        self.id_array_temp.append(idn)
        self.digest_array_temp.append(value)
        return leaf_node

    def update(self, new_id, new_value):  # q+1个区块开始更新
        old_value = self.digest_array_temp.pop(0)
        old_id = self.id_array_temp.pop(0)
        old_leaf_node = self.find_leaf_node(self.root_node, old_value)
        index_to_delete = old_leaf_node.id.index(old_id)  # 要删除的元素的索引
        n_o = old_leaf_node


        old_leaf_node.id.pop(index_to_delete)

        old_leaf_node.value.pop(index_to_delete)

        old_leaf_node.value_hash.pop(index_to_delete)

        combined = zip(old_leaf_node.value, old_leaf_node.id, old_leaf_node.value_hash)
        sorted_tuples = self.merge_sort_tuples(list(combined))
        value_s, id_s, hash_s = zip(*sorted_tuples)
        old_leaf_node.value = list(value_s)
        old_leaf_node.id = list(id_s)
        old_leaf_node.value_hash = list(hash_s)
        while n_o is not None:
            n_o.compute_hash()
            n_o = n_o.parent_node

        new_leaf_node = self.find_leaf_node(self.root_node, new_value)
        new_leaf_node.value.append(new_value)
        new_leaf_node.id.append(new_id)

        hash_of_data = hashlib.sha256(new_id.encode('utf-8')).hexdigest()

        new_leaf_node.value_hash.append(hash_of_data)

        combined = zip(new_leaf_node.value, new_leaf_node.id, new_leaf_node.value_hash)
        sorted_tuples = self.merge_sort_tuples(list(combined))
        value_s, id_s, hash_s = zip(*sorted_tuples)
        new_leaf_node.value = list(value_s)
        new_leaf_node.id = list(id_s)
        new_leaf_node.value_hash = list(hash_s)


        n = new_leaf_node
        while n is not None:
            n.compute_hash()
            n = n.parent_node

        self.id_array_temp.append(new_id)
        self.digest_array_temp.append(new_value)
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

    def merge_sort_tuples(self, arr):
        if len(arr) <= 1:
            return arr

        # 将列表分成两个子列表
        middle = len(arr) // 2
        left_half = arr[:middle]
        right_half = arr[middle:]

        # 递归地对子列表进行排序
        left_half = self.merge_sort_tuples(left_half)
        right_half = self.merge_sort_tuples(right_half)

        # 合并两个有序子列表，按照元组的第一个元素进行比较
        return self.merge_tuples(left_half, right_half)

    def merge_tuples(self, left, right):
        merged = []
        left_index, right_index = 0, 0

        # 比较两个子列表的元素，并将较小的元素添加到 merged 中
        while left_index < len(left) and right_index < len(right):
            if left[left_index][0] < right[right_index][0]:
                merged.append(left[left_index])
                left_index += 1
            else:
                merged.append(right[right_index])
                right_index += 1

        # 将剩余的元素添加到 merged 中
        merged.extend(left[left_index:])
        merged.extend(right[right_index:])

        return merged


    def binary_search_range(self, arr, target_range):
        low = 0
        high = len(arr) - 1
        indices = []

        while low <= high:
            mid = (low + high) // 2

            if target_range[0] <= arr[mid] <= target_range[1]:
                # 在左半部分继续搜索匹配元素
                left = mid - 1
                while left >= low and target_range[0] <= arr[left] <= target_range[1]:
                    indices.append(left)
                    left -= 1
                indices.append(mid)
                # 在右半部分继续搜索匹配元素
                right = mid + 1
                while right <= high and target_range[0] <= arr[right] <= target_range[1]:
                    indices.append(right)
                    right += 1
                return indices
            elif arr[mid] > target_range[1]:
                high = mid - 1
            else:
                low = mid + 1

        return indices  # 返回空列表，表示未找到符合范围的元素

    def range_query(self, id_set, query_start, query_end):
        return self._range_query(self.root_node, id_set, query_start, query_end)

    result = []
    vo_1 = []

    def _range_query(self, node, id_set, query_start, query_end):
        target_range = (query_start, query_end)
        if node.is_leaf_node():
            if node.range_end < query_start or node.range_start > query_end:
                # Pruned node
                pass

            else:

                indices = self.binary_search_range(node.value, target_range)
                a = []
                for index in indices:
                    a.append(node.id[index])
                for idn in id_set:
                    if str(idn) in a:
                        self.result.append(str(idn))



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
                self.vo_1.append(node.r)
                self.vo_1.append(node.hash_value)

            else:
                self.vo_1.append(node.r)
                num = len(node.value_hash) // self.segmentation

                grouped_data = []
                group = []
                for item in node.id:

                    group.append(item)
                    if len(group) == num:
                        grouped_data.append(group)
                        group = []

                # 处理最后一组元素不足3个的情况
                if len(group) > 0:
                    grouped_data.append(group)
                flag = [0] * len(grouped_data)

                for i, j in enumerate(grouped_data):
                    for value in self.result:
                        if value in j:
                            flag[i] = 1
                            break
                        else:
                            continue
                add_array = []
                for m, n in enumerate(flag):
                    i = grouped_data[m]
                    a = []
                    if n == 0:
                        c = ''
                        for j in i:
                            c += hashlib.sha256(j.encode('utf-8')).hexdigest()
                        add_array.append(hashlib.sha256(c.encode('utf-8')).hexdigest())
                    else:
                        for item in i:
                            k = node.id.index(item)
                            if node.id[k] in self.result:
                                a.append(node.id[k])
                            else:
                                a.append(node.value_hash[k])

                        add_array.append(a)
                self.vo_1.append(add_array)


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

    def verify(self, vo_1):
        re = self.hash_root(vo_1)
        ch = self.root_node.hash_value
        return re == ch

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
                if type(e1) is list:
                    ss = ''
                    for item in e1:
                        if type(item) is list:
                            c = ''
                            for i in item:
                                if len(i) != 64:
                                    c += hashlib.sha256(i.encode("utf-8")).hexdigest()

                                else:
                                    c += i
                            ss += hashlib.sha256(c.encode("utf-8")).hexdigest()
                        else:
                            ss += item
                    s += str(e) + hashlib.sha256(ss.encode("utf-8")).hexdigest()
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

    def tree_node_content(self):
        node = [self.root_node]
        node_content = []
        while node:
            n = node.pop(0)
            node_content.append(n.r)
            if n.left_child and n.middle_child and n.right_child:
                node.append(n.left_child)
                node.append(n.middle_child)
                node.append(n.right_child)
            if n.left_child and n.right_child:
                node_content.append(n.hash_value)
            else:
                node_content.append(n.hash_value)
                node_content.append(n.value)
                node_content.append(n.id)
                node_content.append(n.value_hash)

        return node_content

    def binary_search_all(self, arr, target):
        low = 0
        high = len(arr) - 1
        indices = []

        while low <= high:
            mid = (low + high) // 2

            if arr[mid] == target:
                indices.append(mid)
                # 在左半部分继续搜索匹配元素
                left = mid - 1
                while left >= low and arr[left] == target:
                    indices.append(left)
                    left -= 1
                # 在右半部分继续搜索匹配元素
                right = mid + 1
                while right <= high and arr[right] == target:
                    indices.append(right)
                    right += 1
                return indices
            elif arr[mid] > target:
                high = mid - 1
            else:
                low = mid + 1

        return indices  # 返回空列表，表示未找到目标元素

