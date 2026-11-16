import ROOT
import sys

def test_copy_sigma():
    # Inicializa o descritor com parâmetros dummy
    celula_original = ROOT.xAOD.CaloDetDescriptor(0.0, 0.0, 0.1, 0.1, 0, 0.0, 0, 0, 25.0, 0, 3, False)
    
    # Injeta um valor de sigma conhecido para validação
    valor_teste = 42.5
    celula_original.setSigma(valor_teste)
    
    # Invoca o método de cópia da classe C++
    celula_copia = celula_original.copy()
    
    # Resultado da validação
    print(f"Sigma na célula Original: {celula_original.sigma()}")
    print(f"Sigma na célula Cópia: {celula_copia.sigma()}")
    
    if celula_copia.sigma() == valor_teste:
        print("[SUCESSO] O método CaloDetDescriptor::copy() preserva a variável sigma.")
        return 0
    else:
        print("[FALHA] A informação de sigma foi perdida durante a cópia.")
        return 1

if __name__ == "__main__":
    sys.exit(test_copy_sigma())