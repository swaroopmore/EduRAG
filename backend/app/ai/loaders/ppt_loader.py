from langchain_community.document_loaders import UnstructuredPowerPointLoader


class PPTLoaderService:

    def load(self, path: str):

        loader = UnstructuredPowerPointLoader(path)

        return loader.load()