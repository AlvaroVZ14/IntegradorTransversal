"""SMTP y API simulados: ninguna prueba envía un correo real."""
from unittest import TestCase
from unittest.mock import Mock
from scripts.avisos_solicitud import enviar,procesar

class AvisosTests(TestCase):
    def aviso(self):return dict(id='id-ficticio',lease='reserva-ficticia',destinatario='duena@example.test',codigo='MF-2026-0001',contacto='Camila Ficticia',email='cliente@example.test')
    def settings(self):return dict(remitente='avisos@example.test',host='smtp.example.test',usuario='usuario-ficticio',password='clave-ficticia',puerto=587)
    def test_tls_destinatario_y_error_antes_y_despues_de_enviar(self):
        smtp=Mock();smtp.__enter__=Mock(return_value=smtp);smtp.__exit__=Mock(return_value=False);smtp.send_message.return_value={}
        factory=Mock(return_value=smtp)
        self.assertEqual(enviar(self.aviso(),self.settings(),factory),'enviado')
        smtp.starttls.assert_called_once()
        msg=smtp.send_message.call_args.args[0]
        self.assertEqual(msg['To'],'duena@example.test');self.assertIn('MF-2026-0001',msg['Subject'])
        smtp.send_message.side_effect=ConnectionError('simulación después de DATA')
        self.assertEqual(enviar(self.aviso(),self.settings(),factory),'incierto')
        factory.side_effect=ConnectionError('simulación de conexión')
        self.assertEqual(enviar(self.aviso(),self.settings(),factory),'error')
        self.assertEqual(enviar(dict(self.aviso(),destinatario='mal\r\nBcc:otro@example.test'),self.settings(),factory),'error')
    def test_confirmacion_con_reserva_y_sin_reenvio_ciego(self):
        api=Mock(side_effect=[[self.aviso()],True]);mailer=Mock(return_value='error')
        self.assertEqual(procesar(self.settings(),api,mailer),dict(enviado=0,error=1,incierto=0))
        self.assertEqual(api.call_args.args[1]['p_estado'],'error')
        api=Mock(side_effect=[[self.aviso()],ConnectionError('confirmación perdida')]);mailer=Mock(return_value='enviado')
        with self.assertRaises(ConnectionError):procesar(self.settings(),api,mailer)
        mailer.assert_called_once()
