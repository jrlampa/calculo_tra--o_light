// mockData.js — Dados de exemplo para usabilidade (não há cálculo real)

export const dadosCabecalho = {
  orgao: 'ENEL',
  ns: 'NS-001',
  projeto: 'COSMO LDA NOVA 03',
  ponto: 'POSTE 1D',
  endereco: 'RUA EXEMPLO, 123 - BAIRRO',
  estudadoPor: 'J. SILVA',
  matricula: '12345',
  data: '18/03/2026',
};

export const dadosPoste = {
  tipoPoste: 'Concreto Duplo T',
  modeloPoste: '11/300',
  cargaNominal: 300,
};

export const tracaoTotal = 0;

// Dados mock para cada nível — 4 travessias (T1..T4)
const emptyTravessia = {
  tipoRede: '',
  tipoCabo: '',
  vao: '',
  flecha: '',
  angulo: '',
  alturaPoste: '',
  alturaAncoragem: '',
};

export const dadosMT1 = {
  travessias: [
    { tipoRede: 'MT-CA', tipoCabo: 'ACSR 185', vao: '80', flecha: '1,5', angulo: '10', alturaPoste: '11', alturaAncoragem: '10,2' },
    { tipoRede: 'MT-CA', tipoCabo: 'ACSR 185', vao: '95', flecha: '1,8', angulo: '5', alturaPoste: '11', alturaAncoragem: '10,2' },
    { ...emptyTravessia },
    { ...emptyTravessia },
  ],
  tracaoNivel: 'daN °',
};

export const dadosMT2 = {
  travessias: [
    { tipoRede: 'MT-CA', tipoCabo: 'ACSR 95', vao: '80', flecha: '1,2', angulo: '10', alturaPoste: '11', alturaAncoragem: '8,5' },
    { tipoRede: 'MT-CA', tipoCabo: 'ACSR 95', vao: '95', flecha: '1,4', angulo: '5', alturaPoste: '11', alturaAncoragem: '8,5' },
    { ...emptyTravessia },
    { ...emptyTravessia },
  ],
  tracaoNivel: 'daN °',
};

export const dadosBT = {
  travessias: [
    { tipoRede: 'BT-CA', tipoCabo: 'CAA 50', vao: '60', flecha: '1,0', angulo: '15', alturaPoste: '11', alturaAncoragem: '6,5' },
    { tipoRede: 'BT-CA', tipoCabo: 'CAA 50', vao: '70', flecha: '1,2', angulo: '0', alturaPoste: '11', alturaAncoragem: '6,5' },
    { ...emptyTravessia },
    { ...emptyTravessia },
  ],
  tracaoNivel: 'daN °',
};

export const dadosRamaisBTZero = {
  travessias: [
    { qtdLigacoes: '3', vao: '25', flecha: '0,5', angulo: '90', alturaPoste: '11', alturaAncoragem: '5,0' },
    { qtdLigacoes: '1', vao: '20', flecha: '0,4', angulo: '45', alturaPoste: '11', alturaAncoragem: '5,0' },
    { qtdLigacoes: '', vao: '', flecha: '', angulo: '', alturaPoste: '', alturaAncoragem: '' },
    { qtdLigacoes: '', vao: '', flecha: '', angulo: '', alturaPoste: '', alturaAncoragem: '' },
  ],
  tracaoNivel: 'daN °',
};

export const dadosRamaisLigacao = {
  travessias: [
    { tipoCabo: 'CA 10', qtdCabos: '3', vao: '15', flecha: '0,3', angulo: '90', alturaPoste: '11', alturaAncoragem: '4,5' },
    { tipoCabo: 'CA 10', qtdCabos: '2', vao: '12', flecha: '0,2', angulo: '45', alturaPoste: '11', alturaAncoragem: '4,5' },
    { tipoCabo: '', qtdCabos: '', vao: '', flecha: '', angulo: '', alturaPoste: '', alturaAncoragem: '' },
    { tipoCabo: '', qtdCabos: '', vao: '', flecha: '', angulo: '', alturaPoste: '', alturaAncoragem: '' },
  ],
  tracaoNivel: 'daN °',
};

// Tabela R x Carga Nominal do poste
export const tabelaCargas = [
  { alpha: '-', R300: 300, R600: 600 },
  { alpha: 0,   R300: 300, R600: 600 },
  { alpha: 5,   R300: 299, R600: 598 },
  { alpha: 10,  R300: 288, R600: 577 },
  { alpha: 15,  R300: 278, R600: 556 },
  { alpha: 20,  R300: 268, R600: 536 },
  { alpha: 25,  R300: 259, R600: 517 },
  { alpha: 30,  R300: 250, R600: 499 },
  { alpha: 40,  R300: 232, R600: 464 },
  { alpha: 50,  R300: 216, R600: 432 },
  { alpha: 60,  R300: 201, R600: 402 },
  { alpha: 70,  R300: 187, R600: 374 },
  { alpha: 80,  R300: 174, R600: 348 },
  { alpha: 90,  R300: 150, R600: 300 },
];

// Ângulos para o relógio (sentido horário a partir do Norte=90°)
// Representa os ângulos em graus que aparecem no relógio do Excel
export const angulosRelogio = [0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 140, 150, 165, 180, 195, 210, 225, 255, 270, 285, 300, 315, 330, 345, 360];

// Vetores de tração (mock) para desenhar no relógio
export const vetoresTracao = [
  { angulo: 0,   magnitude: 0.7, label: 'T1-MT1' },
  { angulo: 180, magnitude: 0.9, label: 'T2-MT1' },
  { angulo: 10,  magnitude: 0.5, label: 'T1-BT'  },
  { angulo: 190, magnitude: 0.4, label: 'T2-BT'  },
];

// Resultante (mock)
export const resultante = { angulo: 5, magnitude: 1.0 };
