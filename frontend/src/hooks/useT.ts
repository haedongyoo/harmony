import translations, { type Translations } from '../i18n/translations'
import { useLangStore } from '../stores/langStore'

export function useT(): Translations {
  const lang = useLangStore((s) => s.lang)
  return translations[lang]
}
