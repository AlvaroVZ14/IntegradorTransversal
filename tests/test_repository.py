from types import SimpleNamespace
import unittest
from unittest.mock import Mock

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
    def test_composite_rpc_arrays_are_normalized_and_empty_results_fail(self):
        from servicios.repositorio import fila_rpc
        row={'id':'cotizacion','version':2}
        self.assertEqual(fila_rpc([row]),row)
        self.assertEqual(fila_rpc(row),row)
        for respuesta in ([],{},[row,row],None):
            with self.assertRaises(RuntimeError):fila_rpc(respuesta)
        client=Mock();client.rpc.return_value.execute.return_value.data=[row]
        repo=Repository(client,SimpleNamespace(id='owner'),{'rol':'admin'})
        self.assertEqual(repo.save_quote_draft('caso',{},1),row)
        self.assertEqual(repo.issue_quote({'id':'caso','version':1},{},'operacion'),row)

    def test_client_submission_uses_only_rpc(self):
        client=Mock()
        client.rpc.return_value.execute.return_value.data={'codigo':'MF-2026-0001'}
        repo=Repository(client,SimpleNamespace(id='a'),{'rol':'cliente'})
        self.assertEqual(repo.create_request({'consentimiento':True},'request-id'),{'codigo':'MF-2026-0001'})
        client.table.assert_not_called()
        client.rpc.assert_called_once_with('registrar_solicitud',{'p_solicitud_id':'request-id','p_datos':{'consentimiento':True}})

    def test_pagination_reads_more_than_1000_rows(self):
        client=QueryClient([{'id':str(i)} for i in range(1201)])
        repo=Repository(client,SimpleNamespace(id='owner'),{'rol':'admin'})
        self.assertEqual(len(repo.cases()),1201)
        self.assertEqual(client.calls,[(0,499),(500,999),(1000,1499)])

    def test_client_filter_and_owner_actions(self):
        client=QueryClient([{'id':'a','cliente_id':'a'},{'id':'b','cliente_id':'b'}])
        repo=Repository(client,SimpleNamespace(id='a'),{'rol':'cliente'})
        for action in [repo.cases,repo.sales,repo.tariffs,repo.profiles,lambda: repo.quotes('a'),lambda: repo.rows('mf_casos')]:
            with self.assertRaises(PermissionError): action()

    def test_each_confirmed_write_invalidates_cache_and_returns_updated_row(self):
        from unittest.mock import patch
        from datetime import date
        client=Mock()
        row={'id':'caso','version':2}
        client.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value.data=[row]
        client.rpc.return_value.execute.return_value.data=row
        repo=Repository(client,SimpleNamespace(id='owner'),{'rol':'admin'})
        with patch('servicios.dashboard_cache.invalidar_dashboard') as invalidate:
            self.assertEqual(repo.update_case({'id':'caso','version':1},{'contacto':'Daniela Soto'}),row)
            self.assertEqual(repo.update_sale({'id':'venta','version':1},'Pagado',False),row)
            self.assertEqual(repo.issue_quote({'id':'caso','version':1},{},'operacion'),row)
            self.assertEqual(repo.record_sale({'id':'caso'},{'id':'cotizacion'},date(2026,10,22),'Pendiente'),row)
            self.assertEqual(invalidate.call_count,4)


if __name__ == '__main__': unittest.main()
