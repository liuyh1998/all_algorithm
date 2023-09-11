import hashlib


class MerkleNode:
    def __init__(self, data):
        self.data = data
        self.left = None
        self.right = None
        self.value = None


def build_merkle_tree(q):
    height = 0
    nodes = [MerkleNode('_') for _ in range(q)]
    for n in nodes:
        g = n.data
        n.value = g
        n.data = hashlib.sha256(g.encode('utf-8')).hexdigest()

    while len(nodes) > 1:
        parent_level = []
        for i in range(0, len(nodes) - 1, 2):
            data = nodes[i].data + nodes[i + 1].data
            hash_value = hashlib.sha256(data.encode()).hexdigest()
            parent_node = MerkleNode(hash_value)
            parent_node.left = nodes[i]
            parent_node.right = nodes[i + 1]
            parent_level.append(parent_node)

        if len(nodes) % 2 == 1:
            parent_level.append(nodes[-1])

        nodes = parent_level
        height += 1
    return nodes[0]


def calculate_merkle_root(q):
    merkle_tree = build_merkle_tree(q)
    return merkle_tree if merkle_tree else None


def find_leaf(data_id, node, q):

    loc = data_id % q
    binary_str = f'{loc:13b}'  #
    v = []
    for bit in binary_str:
        v.append(bit)
    return _find_leaf(v, node)


def _find_leaf(array, node):
    vo = []
    vo.append('[')
    n = node
    if n.right is not None and n.left is not None:
        w = array.pop(0)

        if w == '1':
            if n.left.value is not None and n.right.value is not None:
                vo.append(n.left.data)
                vo.append('[')
                vo.append(n.right.value)
                vo.append(']')
            else:
                vo.append(n.left.data)
                vo.extend(_find_leaf(array, n.right))  # 递归调用时传入修改后的数组
        else:
            if n.left.value is not None and n.right.value is not None:

                vo.append('[')
                vo.append(n.left.value)
                vo.append(']')
                vo.append(n.right.data)
            else:

                vo.extend(_find_leaf(array, n.left))  # 递归调用时传入修改后的数组
                vo.append(n.right.data)

        vo.append(']')
    return vo


def verify_root(vo):
    global global_var
    str1 = ''
    while vo:
        e = str(vo.pop(0))
        if len(e) == 64:
            str1 += e
        elif e == '[':
            hash_value = verify_root(vo)
            str1 += hash_value
        elif e == ']':
            return hashlib.sha256(str1.encode('utf-8')).hexdigest()
        else:
            str1 += e

    return str1


def find_leaf_update(val, node):
    n = node
    for bit in val:
        if bit == '1':
            n = n.right
        else:
            n = n.left
    return n


def find_l(idn, node, q):
    loc = idn % q
    binary_str = f'{loc:13b}'  #
    v = []
    for bit in binary_str:
        v.append(bit)
    n = find_leaf_update(v, node)
    return n


def update_data(data_id, q, root_node, data):
    loc = data_id % q
    binary_str = f'{loc:13b}'
    v = []
    for bit in binary_str:
        v.append(bit)
    n = find_leaf_update(v, root_node)
    n.value = data
    n.data = hashlib.sha256(str(data).encode('utf-8')).hexdigest()
    update_relate(v, root_node)
    pr = update_proof(v, root_node)

    t, hl = re_comp_root_hash(pr)
    return t, hl


def update_relate(val, node):
    l = len(val)
    while l:
        n = node
        yy = val[:l - 1]
        for bit in yy:
            if n is None:
                # 如果 n 为 None，则无法访问 n.left 或 n.right，直接退出循环
                return
            if bit == '1':
                n = n.right
            else:
                n = n.left

        if n is None:
            # 如果在更新 n 后 n 变为 None，则无法访问 n.left 或 n.right，直接退出循环
            return

        n_l = n.left
        n_r = n.right
        data_1 = n_l.data + n_r.data
        n.data = hashlib.sha256(data_1.encode()).hexdigest()
        l = l - 1
        data_2 = node.left.data + node.right.data
        node.data = hashlib.sha256(data_2.encode()).hexdigest()

def update_proof(array, node):
    pr = []
    pr.append('[')
    n = node
    if n.right is not None and n.left is not None:
        w = array.pop(0)

        if w == '1':
            if n.left.value is not None and n.right.value is not None:
                pr.append(n.left.data)
                pr.append('[')
                pr.append(n.right.value)
                pr.append(']')
            else:
                pr.append(n.left.data)
                pr.extend(_find_leaf(array, n.right))  # 递归调用时传入修改后的数组
        else:
            if n.left.value is not None and n.right.value is not None:

                pr.append('[')
                pr.append(n.left.value)
                pr.append(']')
                pr.append(n.right.data)
            else:
                pr.append(n.right.data)
                pr.extend(_find_leaf(array, n.left))  # 递归调用时传入修改后的数组

        pr.append(']')
    return pr


def re_comp_root_hash(pr, hash_list=None):
    if hash_list is None:
        hash_list = []

    str1 = ''

    while pr:
        e = pr.pop(0)
        if len(str(e)) == 64:
            str1 += e
        elif e == '[':
            hash_value = re_comp_root_hash(pr, hash_list)  # 递归调用，将哈希值列表传递给下一层递归
            str1 += hash_value
        elif e == ']':
            hash_value = hashlib.sha256(str1.encode('utf-8')).hexdigest()
            hash_list.append(hash_value)  # 将哈希值添加到列表中
            return hash_value
        else:
            str1 += str(e)

    return str1, hash_list  # 返回哈希值列表
