import grpc
import vector_index_pb2
import vector_index_pb2_grpc
import numpy as np
import vector_index
from typing import List
import custom_logger
import index_network_config


class VectorIndexClient:
    '''

        This class manages a connection to a vector index over gRPC
    
    '''

    def __init__(self, model_name):
        self.logger = custom_logger.Logger(f"VectorIndexClient[{model_name}]")
        self.logger.verbose = True


        port = index_network_config.port_map[model_name]
        
        # on the index network, the domain name for vector index server is the model whose embeddings it serves
        service_route = f'{model_name}_service:{port}'
        self.logger.log(f"initializing client for service: {service_route}")

        self.channel = grpc.insecure_channel(service_route)
        self.stub = vector_index_pb2_grpc.VectorIndexStub(self.channel)
    
    def upsert(self, vector: np.array, payload: vector_index.VectorPayload):
        '''
        Upserts the point to the vector index, with its corresponding payload
        '''
       
        payload_proto = vector_index_pb2.VectorPayload(**payload.__dict__)

        upsert_request_proto = vector_index_pb2.UpsertRequest(
            payload = payload_proto,
            nparray_bytes = vector.tobytes()
        )

        upsert_response = self.stub.Upsert(upsert_request_proto)

        return upsert_response.status
    
    def search(self, vector: np.array) -> List[vector_index.SearchResult]:
        # This method is not finished
        # it needs to convert the search_response
        # into the suggested return type
        search_request_proto = vector_index_pb2.SearchRequest(nparray_bytes=vector.tobytes())

        search_response = self.stub.Search(search_request_proto)

        print(search_response)

 
if __name__ == "__main__":

    client = VectorIndexClient("sample")

    sample_vector = np.random.randn(128).astype(np.float32)

    sample_payload = vector_index.VectorPayload(
        text_section_idx=-1,
        image_url="image",
        page_url="some page"
    )
    client.upsert(sample_vector, sample_payload)
    #client.search(sample_vector)