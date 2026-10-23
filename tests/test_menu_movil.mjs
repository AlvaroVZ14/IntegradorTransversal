// Comprueba el cierre complementario sin navegador ni datos de Supabase.
import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';

const source = readFileSync(new URL('../utils/navegacion.py', import.meta.url), 'utf8');
const js = source.match(/js="""([\s\S]*?)"""/)[1];
let mobile = false, expanded = true, hasButton = true, clicks = 0;
const listeners = new Map(), frames = [];
class Element {
  constructor(inMenu = true) { this.inMenu = inMenu; }
  closest() { return this.inMenu ? this : null; }
}
const sidebar = { querySelector: () => hasButton ? { click() { clicks++; expanded = false; } } : null };
const document = {
  addEventListener: (event, listener) => listeners.set(event, listener),
  removeEventListener: (event, listener) => {
    assert.equal(listeners.get(event), listener);
    listeners.delete(event);
  },
  querySelector: () => expanded ? sidebar : null,
};
const window = { matchMedia: () => ({ get matches() { return mobile; } }) };
const mount = new Function('window', 'document', 'Element', 'requestAnimationFrame',
  js.replace('export default function()', 'return function()'));
const cleanup = mount(window, document, Element, callback => frames.push(callback))();
const click = (changes = {}) => listeners.get('click')({ target: new Element(), button: 0,
  ctrlKey: false, metaKey: false, shiftKey: false, altKey: false, ...changes });
const flush = () => { while (frames.length) frames.shift()(); };

click(); flush(); assert.equal(clicks, 0); // Escritorio conserva el menú.
mobile = true;
click(); assert.equal(clicks, 0); flush(); assert.equal(clicks, 1); // Después del enlace nativo.
click(); flush(); assert.equal(clicks, 1); // No reabre un menú ya cerrado.
expanded = true;
click(); expanded = false; flush(); assert.equal(clicks, 1); // El cierre nativo se adelantó.
expanded = true;
click({ target: new Element(false) }); flush(); assert.equal(clicks, 1); // Otro control.
click({ ctrlKey: true }); flush(); assert.equal(clicks, 1); // Abrir en otra pestaña.
click({ button: 1 }); flush(); assert.equal(clicks, 1); // Botón central.
click({ target: null }); flush(); assert.equal(clicks, 1); // Evento ajeno a un elemento.
hasButton = false;
click(); assert.doesNotThrow(flush); assert.equal(clicks, 1); // Selector ausente: sin efecto.
cleanup(); assert.equal(listeners.size, 0); // No acumula eventos al cambiar de página.
console.log('10 escenarios de cierre móvil aprobados.');
