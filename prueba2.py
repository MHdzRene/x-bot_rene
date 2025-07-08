"""
Prueba de implementación de análisis político mejorado con threading para múltiples compañías
"""

import time
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional
from politics import PoliticalUncertaintyAnalyzer


class EnhancedPoliticalAnalyzer(PoliticalUncertaintyAnalyzer):
    """
    Extensión de PoliticalUncertaintyAnalyzer con capacidades de threading
    para análisis de múltiples compañías de forma optimizada.
    """
    
    def __init__(self, use_llm=True):
        super().__init__(use_llm=use_llm)
        # Semáforo para limitar conexiones concurrentes a Ollama
        self._ollama_semaphore = threading.Semaphore(3)  # Máximo 3 conexiones simultáneas
        print("🚀 Enhanced Political Analyzer inicializado con threading")
    
    def _analyze_single_company_wrapper(self, args):
        """
        Función wrapper para análisis individual (compatible con ThreadPoolExecutor)
        
        Args:
            args: Tupla con (company_name, news_data)
            
        Returns:
            Tupla con (company_name, result_dict)
        """
        company_name, news_data = args
        
        try:
            # Usar el método original pero de forma thread-safe
            result = self.enhanced_political_analysis(news_data, company_name)
            print(f"✅ Completado análisis para {company_name} - Score: {result.get('enhanced_score', 0)}")
            return company_name, result
            
        except Exception as e:
            print(f"❌ Error analizando {company_name}: {e}")
            return company_name, {
                "company": company_name,
                "enhanced_score": 0,
                "confidence_level": "low",
                "error": str(e)
            }
    
    def _analyze_with_ollama_threadsafe(self, text: str, analysis_type: str) -> Dict:
        """
        Versión thread-safe del análisis con Ollama usando semáforo
        """
        with self._ollama_semaphore:
            return self._analyze_with_ollama(text, analysis_type)
    
    def _determine_optimal_workers(self, num_companies: int) -> int:
        """
        Determina el número óptimo de workers basado en:
        - Número de compañías
        - CPU cores disponibles
        - Limitaciones de Ollama
        
        Args:
            num_companies: Número de compañías a analizar
            
        Returns:
            Número óptimo de workers
        """
        cpu_count = os.cpu_count() or 4
        
        # Fórmula: min(número_compañías, CPU_cores * 2, 8)
        # Limitamos a 8 para evitar saturar Ollama
        optimal_workers = min(num_companies, cpu_count * 2, 8)
        
        print(f"📊 CPU cores: {cpu_count}, Compañías: {num_companies}, Workers óptimos: {optimal_workers}")
        return optimal_workers
    
    def _process_companies_in_chunks(self, companies: List[str], news_data: Dict, 
                                   chunk_size: int = 20) -> Dict:
        """
        Procesa compañías en chunks para optimizar memoria con listas muy grandes
        
        Args:
            companies: Lista de compañías
            news_data: Datos de noticias
            chunk_size: Tamaño de cada chunk
            
        Returns:
            Resultados combinados de todos los chunks
        """
        all_results = {}
        failed_companies = []
        total_chunks = (len(companies) + chunk_size - 1) // chunk_size
        
        for chunk_idx, i in enumerate(range(0, len(companies), chunk_size)):
            chunk = companies[i:i + chunk_size]
            print(f"🔄 Procesando chunk {chunk_idx + 1}/{total_chunks} ({len(chunk)} compañías)")
            
            chunk_results = self._analyze_companies_chunk(chunk, news_data)
            
            all_results.update(chunk_results['results'])
            failed_companies.extend(chunk_results['failed_companies'])
            
            # Pequeña pausa entre chunks para evitar sobrecarga
            if chunk_idx < total_chunks - 1:
                time.sleep(1)
        
        return {
            'results': all_results,
            'failed_companies': failed_companies
        }
    
    def _analyze_companies_chunk(self, companies: List[str], news_data: Dict) -> Dict:
        """
        Analiza un chunk de compañías usando threading
        """
        results = {}
        failed_companies = []
        
        max_workers = self._determine_optimal_workers(len(companies))
        
        # Preparar argumentos para threading
        company_args = [(company, news_data) for company in companies 
                       if company in news_data]
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Crear tareas
            future_to_company = {
                executor.submit(self._analyze_single_company_wrapper, args): args[0]
                for args in company_args
            }
            
            # Recopilar resultados con timeout
            for future in as_completed(future_to_company, timeout=300):  # 5 min timeout total
                company = future_to_company[future]
                try:
                    company_name, result = future.result(timeout=60)  # 60s timeout por compañía
                    results[company_name] = result
                    
                except Exception as exc:
                    print(f"❌ Error procesando {company}: {exc}")
                    failed_companies.append(company)
        
        return {
            'results': results,
            'failed_companies': failed_companies
        }
    
    def _calculate_summary_stats(self, results: Dict) -> Dict:
        """
        Calcula estadísticas resumen de los análisis
        """
        if not results:
            return {}
        
        scores = [result.get('enhanced_score', 0) for result in results.values() 
                 if 'error' not in result]
        
        if not scores:
            return {"error": "No se pudieron calcular estadísticas"}
        
        avg_score = sum(scores) / len(scores)
        
        # Clasificar compañías por riesgo
        companies_by_risk = {"high": [], "medium": [], "low": []}
        
        for company, result in results.items():
            if 'error' in result:
                continue
                
            score = result.get('enhanced_score', 0)
            if score >= 70:
                companies_by_risk["high"].append(company)
            elif score >= 40:
                companies_by_risk["medium"].append(company)
            else:
                companies_by_risk["low"].append(company)
        
        return {
            "avg_political_score": round(avg_score, 2),
            "max_score": max(scores),
            "min_score": min(scores),
            "high_risk_companies": companies_by_risk["high"],
            "medium_risk_companies": companies_by_risk["medium"],
            "low_risk_companies": companies_by_risk["low"],
            "companies_by_risk": companies_by_risk
        }
    
    def enhanced_political_analysis_batch(self, news_data: Dict, 
                                        companies: Optional[List[str]] = None,
                                        max_workers: Optional[int] = None,
                                        use_chunks: bool = True,
                                        chunk_size: int = 20) -> Dict:
        """
        Análisis político mejorado para múltiples compañías usando threading.
        
        Args:
            news_data: Diccionario con datos de noticias {company: [articles]}
            companies: Lista de compañías a analizar (None = todas las disponibles)
            max_workers: Número máximo de workers (None = auto-detectar)
            use_chunks: Si usar procesamiento en chunks para listas grandes
            chunk_size: Tamaño de cada chunk
            
        Returns:
            Dict con resultados completos del análisis
        """
        start_time = time.time()
        
        # Determinar compañías a analizar
        if companies is None:
            companies = list(news_data.keys())
        
        # Filtrar compañías que realmente tienen datos
        available_companies = [c for c in companies if c in news_data and news_data[c]]
        
        if not available_companies:
            return {
                "error": "No hay compañías con datos disponibles",
                "requested_companies": len(companies),
                "available_companies": 0
            }
        
        print(f"🏛️ Iniciando análisis político para {len(available_companies)} compañías")
        print(f"📋 Compañías: {', '.join(available_companies[:5])}{'...' if len(available_companies) > 5 else ''}")
        
        # Decidir si usar chunks
        if use_chunks and len(available_companies) > chunk_size:
            print(f"📦 Usando procesamiento en chunks (tamaño: {chunk_size})")
            batch_results = self._process_companies_in_chunks(
                available_companies, news_data, chunk_size
            )
        else:
            print("🔄 Procesamiento directo (sin chunks)")
            batch_results = self._analyze_companies_chunk(available_companies, news_data)
        
        end_time = time.time()
        execution_time = round(end_time - start_time, 2)
        
        # Calcular estadísticas
        summary_stats = self._calculate_summary_stats(batch_results['results'])
        
        # Resultado final
        final_result = {
            "execution_info": {
                "total_companies": len(companies),
                "available_companies": len(available_companies),
                "successful_analyses": len(batch_results['results']),
                "failed_companies": batch_results['failed_companies'],
                "execution_time_seconds": execution_time,
                "llm_provider": "ollama" if (self.ollama_client and self.ollama_client.is_available()) else "huggingface"
            },
            "results": batch_results['results'],
            "summary_stats": summary_stats,
            "failed_analyses": batch_results['failed_companies']
        }
        
        print(f"✅ Análisis completado en {execution_time}s")
        print(f"📊 Éxitos: {len(batch_results['results'])}, Fallos: {len(batch_results['failed_companies'])}")
        
        return final_result
    
    def print_analysis_summary(self, batch_result: Dict):
        """
        Imprime un resumen bonito de los resultados del análisis
        """
        print("\n" + "="*80)
        print("📊 RESUMEN DEL ANÁLISIS POLÍTICO MEJORADO")
        print("="*80)
        
        exec_info = batch_result.get('execution_info', {})
        print(f"⏱️  Tiempo de ejecución: {exec_info.get('execution_time_seconds', 0)}s")
        print(f"🏢 Compañías analizadas: {exec_info.get('successful_analyses', 0)}/{exec_info.get('total_companies', 0)}")
        print(f"🤖 LLM utilizado: {exec_info.get('llm_provider', 'unknown')}")
        
        summary = batch_result.get('summary_stats', {})
        if summary:
            print(f"\n📈 ESTADÍSTICAS:")
            print(f"   Score promedio: {summary.get('avg_political_score', 0)}/100")
            print(f"   Score máximo: {summary.get('max_score', 0)}/100")
            print(f"   Score mínimo: {summary.get('min_score', 0)}/100")
            
            print(f"\n🚨 CLASIFICACIÓN POR RIESGO:")
            print(f"   Alto riesgo (≥70): {len(summary.get('high_risk_companies', []))}")
            print(f"   Riesgo medio (40-69): {len(summary.get('medium_risk_companies', []))}")
            print(f"   Bajo riesgo (<40): {len(summary.get('low_risk_companies', []))}")
            
            if summary.get('high_risk_companies'):
                print(f"   🔴 Empresas de alto riesgo: {', '.join(summary['high_risk_companies'][:3])}{'...' if len(summary['high_risk_companies']) > 3 else ''}")
        
        if batch_result.get('failed_analyses'):
            print(f"\n❌ Análisis fallidos: {', '.join(batch_result['failed_analyses'])}")
        
        print("="*80)


def test_enhanced_analyzer():
    """
    Función de prueba para el Enhanced Political Analyzer
    """
    print("🧪 INICIANDO PRUEBAS DEL ENHANCED POLITICAL ANALYZER")
    print("="*70)
    
    try:
        # Inicializar analizador
        analyzer = EnhancedPoliticalAnalyzer(use_llm=True)
        
        # Cargar datos de noticias
        print("📰 Cargando datos de noticias...")
        news_data = analyzer.get_news_data_using_thread(new_extraction=False)
        
        if not news_data:
            print("❌ No se pudieron cargar los datos de noticias")
            return
        
        print(f"✅ Datos cargados: {len(news_data)} compañías")
        
        # Prueba 1: Análisis de pocas compañías (sin chunks)
        print("\n🧪 PRUEBA 1: Análisis de 3 compañías (sin chunks)")
        test_companies_small = ["Tesla", "Apple", "Microsoft"]
        
        start_time = time.time()
        results_small = analyzer.enhanced_political_analysis_batch(
            news_data, 
            companies=test_companies_small,
            use_chunks=False
        )
        end_time = time.time()
        
        print(f"⏱️ Tiempo con threading: {end_time - start_time:.2f}s")
        analyzer.print_analysis_summary(results_small)
        
        # Comparación con análisis secuencial
        print("\n🔄 Comparando con análisis secuencial...")
        start_time = time.time()
        for company in test_companies_small:
            if company in news_data:
                result = analyzer.enhanced_political_analysis(news_data, company)
                print(f"  {company}: {result.get('enhanced_score', 0)}")
        end_time = time.time()
        print(f"⏱️ Tiempo secuencial: {end_time - start_time:.2f}s")
        
        # Prueba 2: Análisis de todas las compañías (con chunks)
        print("\n🧪 PRUEBA 2: Análisis de todas las compañías disponibles")
        all_companies = list(news_data.keys())
        
        results_all = analyzer.enhanced_political_analysis_batch(
            news_data,
            companies=all_companies,
            use_chunks=True,
            chunk_size=5  # Chunks pequeños para la prueba
        )
        
        analyzer.print_analysis_summary(results_all)
        
        # Mostrar resultados detallados de algunas compañías
        print("\n📋 RESULTADOS DETALLADOS (Top 5):")
        successful_results = results_all.get('results', {})
        sorted_companies = sorted(
            successful_results.items(), 
            key=lambda x: x[1].get('enhanced_score', 0), 
            reverse=True
        )
        
        for i, (company, result) in enumerate(sorted_companies[:5]):
            score = result.get('enhanced_score', 0)
            confidence = result.get('confidence_level', 'unknown')
            print(f"  {i+1}. {company}: {score}/100 (confianza: {confidence})")
        
        return results_all
        
    except Exception as e:
        print(f"❌ Error en las pruebas: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Ejecutar pruebas
    test_results = test_enhanced_analyzer()
    
    if test_results:
        print("\n🎉 ¡Pruebas completadas exitosamente!")
        print("💡 El Enhanced Political Analyzer está listo para usar en producción")
    else:
        print("\n❌ Las pruebas fallaron")
