from pymilvus import MilvusClient, DataType, Function, FunctionType


'''
    创建Milvus DB中的collection(相当于关系型数据库的一张表)
'''
def create_collection(client, name):
    return client.create_collection(
        collection_name=name,
        schema=create_schema(client),
        index_params=add_index(client)
    )


'''
    创建数据定义
'''
def create_schema(client):
    schema = client.create_schema(auto_id=False)
    schema.add_field(
        field_name="doc_id", 
        datatype=DataType.INT64, 
        is_primary=True, 
        description="doc id"
    )
    #原始doc文本
    schema.add_field(
        field_name="origin_doc", 
        datatype=DataType.VARCHAR, 
        max_length=1000, 
        enable_analyzer=True, 
        description="raw doc content"
    )
    #原始doc对应的稠密向量
    schema.add_field(
        field_name="doc_dense", 
        datatype=DataType.FLOAT_VECTOR, 
        dim=768, 
        description="doc dense embedding"
    )
    #原始doc对应的稀疏向量
    schema.add_field(
        field_name="doc_sparse", 
        datatype=DataType.SPARSE_FLOAT_VECTOR, 
        description="doc sparse embedding"
    )
    return schema


'''
    为定义好的数据字段添加索引
'''
def add_index(client):
    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="doc_dense",
        index_name="doc_dense_index",
        index_type="AUTOINDEX",
        metric_type="IP"
    )
    index_params.add_index(
        field_name="doc_sparse",
        index_name="doc_sparse_index",
        index_type="SPARSE_INVERTED_INDEX",
        metric_type="IP"
    )
    return index_params