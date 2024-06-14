import os
import request_client
import page_index
import crawl_plan
import custom_logger
import time
import yaml

class CrawlSession: 
    '''

        This object will orchestrate a single crawling process. It is meant to be run in a container, where it will will be initialized, and run. All of the parameters for a crawl session are meant to come from environment variables

    '''
    def __init__(self, crawl_plan_db_path: str, crawl_instruction: str, page_index_path: str, politeness: bool=False):

        # whether or not to be polite to the hosts
        self.politeness = politeness

        # manage HTTP requests
        self.request_client = request_client.RequestClient()

        # manage the crawl_plan
        self.crawl_plan_client = crawl_plan.CrawlPlanDatabaseClient(crawl_plan_db_path)

        # manage the page index
        self.page_index_client = page_index.PageIndexClient(page_index_path)


        self.crawl_instruction = crawl_instruction
        self.start, self.end = self.parse_crawl_instruction(crawl_instruction)


        # logging
        self.logger = custom_logger.Logger("CrawlSession")
        self.logger.verbose = True

    def parse_crawl_instruction(self, crawl_instruction):
        crawl_instruction = crawl_instruction.split('-')
        start, end = crawl_instruction[0], crawl_instruction[1]
        start, end = int(start), int(end)
        return start, end
    
    def process_page(self, page_url: str):
        '''
        Given a URL for a page, upsert the page data for the URL, and its corresponding assets to the page index
        '''
        
        # request and extract the page content
        self.logger.log(f"getting page data for {page_url[-100:]}")

        # load the data for the page
        parse_result = self.request_client.load_page_parse_result(page_url)

        # the data for the page could not be loaded
        if parse_result == None:
            return

        page_data = page_index.PageIndexData(**parse_result.page_dict)

        self.logger.log(f"page has {len(page_data.text_sections)} text sections and {len(page_data.image_urls)} image(s)")

        # add the page data to the index
        self.page_index_client.upsert_page_data(page_data)

        # iterate through each of the images, and upsert each of them into the page index
        for image_url in page_data.image_urls:
            
            # request the bytes for the image 
            self.logger.log(f"\t getting image bytes for {image_url[-50:]}")
            image_bytes = self.request_client.load_image_bytes(image_url)

            if image_bytes != None: 
                # save the image data to the page index
                self.page_index_client.upsert_image_bytes( image_url , image_bytes )

    
    def crawl(self):
        for i in range(self.start, self.end):
            if self.politeness:
                time.sleep(2)
            self.logger.log(f"Crawling url {i}")
            #print(f"{i}/{self.end}")
            url = self.crawl_plan_client.read_url(i)
            self.process_page(url)
        
        # now that crawling has been finished, put an entry in the management file, indicating that the given section has been completed
        log_crawl_session("/project-dir/se-management/wikipedia_v1-sections.yml",self.crawl_instruction)

def log_crawl_session(se_management_path, crawl_instruction):
    with open(se_management_path,'r') as f:
        se_management = yaml.safe_load(f)
    

    se_management['Crawled Sections'].append(crawl_instruction)

    print(f"{se_management}")

    with open(se_management_path,'w') as f:
        yaml.dump(se_management, f)


if __name__ == "__main__":
    '''
    
        This section of the script will be where crawling sessions get initiated from inside their crawling containers. The parameters of the crawl will come from environment variables, which can be set specificially inside of the containers. The nescessary environment variables are: 

            CRAWL_PLAN_DB_PATH: the path to the database for the crawl plan

            CRAWL_INSTRUCTION: a string of the format: "(crawl start)-(crawl end)" 

            PAGE_INDEX_PATH: the path to the page index where the crawled data is stored

            POLITENESS: whether or not to be polite to the hosts

    '''

    # the path to the crawl plan database
    crawl_plan_db_path = os.environ['CRAWL_PLAN_DB_PATH']

    # a string representing what keys to crawl in the crawl session
    crawl_instruction = os.environ['CRAWL_INSTRUCTION']

    # path to the page index
    page_index_path = os.environ['PAGE_INDEX_PATH']

    politeness = bool(os.environ['POLITENESS'])

    print(f"INITIALIZING CRAWL SESSION:\n CRAWL_PLAN_DB_PATH: {crawl_plan_db_path}\n CRAWL_INSTRUCTION: {crawl_instruction}\n PAGE_INDEX_PATH: {page_index_path}\n POLITENESS: {politeness}")

    crawl_session = CrawlSession(crawl_plan_db_path, crawl_instruction, page_index_path, politeness=politeness)

    crawl_session.crawl()