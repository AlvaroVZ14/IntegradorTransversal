from types import SimpleNamespace
import unittest

from mente_futuro.repository import Repository


class QueryClient:
    def __init__(self,rows):
        self.data=rows
        self.calls=[]
        self.filters=[]
    def table(self,table):
        self.filters=[]
        return self
    def select(self,*_): return self
    def eq(self,key,value):
        self.filters.append((key,value))
        return self
    def order(self,*_,**__): return self
    def range(self,start,end):
        self.bounds=(start,end)
        self.calls.append(self.bounds)
        return self
    def execute(self):
        rows=self.data
        for key,value in self.filters:
            rows=[r for r in rows if r.get(key)==value]
        start,end=self.bounds
        return SimpleNamespace(data=rows[start:end+1])


class RepositoryTests(unittest.TestCase):
    def test_pagination_reads_more_than_1000_rows(self):
        client=QueryClient([{'id':str(i)} for i in range(1201)])
        repo=Repository(client,SimpleNamespace(id='owner'),{'rol':'duena'})
        self.assertEqual(len(repo.cases()),1201)
        self.assertEqual(client.calls,[(0,499),(500,999),(1000,1499)])

    def test_client_filter_and_owner_actions(self):
        client=QueryClient([{'id':'a','cliente_id':'a'},{'id':'b','cliente_id':'b'}])
        repo=Repository(client,SimpleNamespace(id='a'),{'rol':'cliente'})
        self.assertEqual([c['id'] for c in repo.cases()],['a'])
        for action in [repo.sales,repo.tariffs,repo.profiles]:
            with self.assertRaises(PermissionError): action()


if __name__ == '__main__': unittest.main()
