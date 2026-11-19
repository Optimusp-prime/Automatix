import { toPayload, type EditorDocument, type ValidationResult } from './model';

export async function validateDocument(document: EditorDocument, signal: AbortSignal): Promise<ValidationResult> {
  const response = await fetch('/api/dfa/validate', { method: 'POST',
    headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(toPayload(document)), signal });
  if (response.status === 422) throw new Error('Données non prises en charge. Limites : 200 états, 128 symboles et 4 000 transitions ; noms de 64 caractères maximum.');
  if (!response.ok) throw new Error('La validation est indisponible. Vérifiez que le serveur Automatix est démarré.');
  const result: unknown = await response.json();
  if (!result || typeof result !== 'object' || !('valid' in result) || typeof result.valid !== 'boolean'
    || !('issues' in result) || !Array.isArray(result.issues)) throw new Error('Réponse inattendue du serveur. Réessayez.');
  return result as ValidationResult;
}
