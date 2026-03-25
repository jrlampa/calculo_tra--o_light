/**
 * Factories reutilizaveis para testes E2E de persistencia.
 */

class ProjetoBuilder {
  constructor() {
    this.data = {
      orgao: 'TEST_ORGAO',
      ns: `NS-${Date.now()}`,
      nome: `TestProjeto${Date.now()}`,
      endereco: 'Rua Teste, 123',
      estudado_por: 'E2E Bot',
      matricula: '9999',
      data_estudo: new Date().toLocaleDateString('pt-BR'),
    };
  }

  withOrgao(orgao) {
    this.data.orgao = orgao;
    return this;
  }

  withNs(ns) {
    this.data.ns = ns;
    return this;
  }

  withNome(nome) {
    this.data.nome = nome;
    return this;
  }

  withEndereco(endereco) {
    this.data.endereco = endereco;
    return this;
  }

  withEstudadoPor(estudadoPor) {
    this.data.estudado_por = estudadoPor;
    return this;
  }

  withMatricula(matricula) {
    this.data.matricula = matricula;
    return this;
  }

  withDataEstudo(dataEstudo) {
    this.data.data_estudo = dataEstudo;
    return this;
  }

  build() {
    return { ...this.data };
  }
}

class PontoBuilder {
  constructor() {
    this.data = {
      ponto: `P${Date.now().toString().slice(-6)}`,
      tipo_poste: 'DT',
      modelo_poste: '11/600',
    };
  }

  withPonto(ponto) {
    this.data.ponto = ponto;
    return this;
  }

  withRunId(runId, prefixo = 'P') {
    this.data.ponto = `${prefixo}${String(runId)}`.replace(/[^a-zA-Z0-9-]/g, '').slice(0, 10);
    return this;
  }

  withTipoPoste(tipoPoste) {
    this.data.tipo_poste = tipoPoste;
    return this;
  }

  withModeloPoste(modeloPoste) {
    this.data.modelo_poste = modeloPoste;
    return this;
  }

  build() {
    return { ...this.data };
  }
}

class TravessiaBuilder {
  constructor(posicao = 1) {
    this.data = {
      posicao,
      tipo_rede: '',
      tipo_cabo: '',
      vao: 0,
      flecha: 0,
      angulo: 0,
      qtd_ligacoes: 0,
      qtd_cabos: 0,
    };
  }

  withTipoRede(tipoRede) {
    this.data.tipo_rede = tipoRede;
    return this;
  }

  withTipoCabo(tipoCabo) {
    this.data.tipo_cabo = tipoCabo;
    return this;
  }

  withVao(vao) {
    this.data.vao = vao;
    return this;
  }

  withFlecha(flecha) {
    this.data.flecha = flecha;
    return this;
  }

  withAngulo(angulo) {
    this.data.angulo = angulo;
    return this;
  }

  withQtdLigacoes(qtdLigacoes) {
    this.data.qtd_ligacoes = qtdLigacoes;
    return this;
  }

  withQtdCabos(qtdCabos) {
    this.data.qtd_cabos = qtdCabos;
    return this;
  }

  build() {
    return { ...this.data };
  }
}

class ResultadoBuilder {
  constructor() {
    this.data = {
      mt1_tracao: 450.5,
      mt1_angulo: 12.3,
      mt2_tracao: 0.0,
      mt2_angulo: 0.0,
      bt_tracao: 0.0,
      bt_angulo: 0.0,
      btz_tracao: 0.0,
      btz_angulo: 0.0,
      ral_tracao: 0.0,
      ral_angulo: 0.0,
      total_tracao: 450.5,
      total_angulo: 12.3,
      poste_ecc: 120.0,
      texto_mt1: 'MT1: 450.5 daN @ 12.3°',
      texto_mt2: '',
      texto_bt: '',
      texto_btz: '',
      texto_ral: '',
      texto_total: 'Total final: 450.5 daN @ 12.3°',
    };
  }

  withMt1Tracao(valor) {
    this.data.mt1_tracao = valor;
    return this;
  }

  withMt1Angulo(valor) {
    this.data.mt1_angulo = valor;
    return this;
  }

  withTotalTracao(valor) {
    this.data.total_tracao = valor;
    return this;
  }

  withTotalAngulo(valor) {
    this.data.total_angulo = valor;
    return this;
  }

  withPosteEcc(valor) {
    this.data.poste_ecc = valor;
    return this;
  }

  withTextoMt1(valor) {
    this.data.texto_mt1 = valor;
    return this;
  }

  withTextoTotal(valor) {
    this.data.texto_total = valor;
    return this;
  }

  build() {
    return { ...this.data };
  }
}

class CalculoPayloadBuilder {
  constructor() {
    this.pontoId = null;
    this.niveis = [];
    this.resultado = null;
  }

  forPonto(pontoId) {
    this.pontoId = pontoId;
    return this;
  }

  withNivelMT1(travessias) {
    this.niveis.push({ nivel: 'MT1', altura_poste: 11.0, altura_ancoragem: 9.2, travessias });
    return this;
  }

  withNivelMT2(travessias) {
    this.niveis.push({ nivel: 'MT2', altura_poste: 10.5, altura_ancoragem: 8.7, travessias });
    return this;
  }

  withNivelBT(travessias) {
    this.niveis.push({ nivel: 'BT', altura_poste: 9.0, altura_ancoragem: 7.5, travessias });
    return this;
  }

  withNivelBTZ(travessias) {
    this.niveis.push({ nivel: 'BTZ', altura_poste: 1.5, altura_ancoragem: 1.0, travessias });
    return this;
  }

  withNivelRAL(travessias) {
    this.niveis.push({ nivel: 'RAL', altura_poste: 8.0, altura_ancoragem: 6.5, travessias });
    return this;
  }

  withResultado(resultado) {
    this.resultado = resultado;
    return this;
  }

  build() {
    return {
      ponto_id: this.pontoId,
      niveis: this.niveis,
      resultado: this.resultado,
    };
  }
}

export const criarProjeto = () => new ProjetoBuilder();
export const criarPonto = () => new PontoBuilder();
export const criarTravessia = (posicao) => new TravessiaBuilder(posicao);
export const criarResultado = () => new ResultadoBuilder();
export const criarCalculoPayload = () => new CalculoPayloadBuilder();
