export const CAMPOS_MT = [
  { campo: 'tipoRede', label: 'Tipo de rede', unidade: '', isDropdown: true, configKey: 'redes' },
  { campo: 'tipoCabo', label: 'Tipo de cabo', unidade: '', isDropdown: true, configKey: 'cabos' },
  { campo: 'vao', label: 'Vão', unidade: 'm' },
  { campo: 'flecha', label: 'Flecha', unidade: 'm' },
  { campo: 'angulo', label: 'Ângulo', unidade: '°' },
  { campo: 'alturaPoste', label: 'Altura poste', unidade: 'm' },
  { campo: 'alturaAncoragem', label: 'Altura ancoragem', unidade: 'm' },
]

export const CAMPOS_BT = CAMPOS_MT

export const CAMPOS_BTZ = [
  { campo: 'qtdLigacoes', label: 'Quantidade de ligações (*)', unidade: '' },
  { campo: 'vao', label: 'Vão', unidade: 'm' },
  { campo: 'flecha', label: 'Flecha', unidade: 'm' },
  { campo: 'angulo', label: 'Ângulo', unidade: '°' },
  { campo: 'alturaPoste', label: 'Altura poste', unidade: 'm' },
  { campo: 'alturaAncoragem', label: 'Altura ancoragem', unidade: 'm' },
]

export const CAMPOS_RAL = [
  { campo: 'tipoCabo', label: 'Tipo de cabo', unidade: '', isDropdown: true, configKey: 'cabos' },
  { campo: 'qtdCabos', label: 'Quantidade de cabos', unidade: '' },
  { campo: 'vao', label: 'Vão', unidade: 'm' },
  { campo: 'flecha', label: 'Flecha', unidade: 'm' },
  { campo: 'angulo', label: 'Ângulo', unidade: '°' },
  { campo: 'alturaPoste', label: 'Altura poste', unidade: 'm' },
  { campo: 'alturaAncoragem', label: 'Altura ancoragem', unidade: 'm' },
]

export const CABECALHO_INICIAL = {
  orgao: '',
  ns: '',
  projeto: '',
  ponto: '',
  endereco: '',
  estudadoPor: '',
  matricula: '',
  data: '',
}

export const POSTE_INICIAL = {
  tipoPoste: '',
  modeloPoste: '',
}

export const TRAVESSIA_MT_VAZIA = {
  tipoRede: '',
  tipoCabo: '',
  vao: '',
  flecha: '',
  angulo: '',
  alturaPoste: '',
  alturaAncoragem: '',
}

export const TRAVESSIA_BTZ_VAZIA = {
  qtdLigacoes: '',
  vao: '',
  flecha: '',
  angulo: '',
  alturaPoste: '',
  alturaAncoragem: '',
}

export const TRAVESSIA_RAL_VAZIA = {
  tipoCabo: '',
  qtdCabos: '',
  vao: '',
  flecha: '',
  angulo: '',
  alturaPoste: '',
  alturaAncoragem: '',
}

export function createTravessiasVazias(template) {
  return Array.from({ length: 4 }, () => ({ ...template }))
}

export function updateTravessia(list, idx, campo, valor) {
  return list.map((travessia, index) => (index === idx ? { ...travessia, [campo]: valor } : travessia))
}
