import { useLangStore } from '../../stores/langStore'

export default function LangToggle() {
  const { lang, toggle } = useLangStore()

  return (
    <button
      onClick={toggle}
      className="flex items-center gap-1.5 px-3 py-1.5 bg-studio-panel border border-studio-border hover:border-studio-accent rounded-xl text-sm transition-colors"
      aria-label="Toggle language"
    >
      <span className={lang === 'ko' ? 'text-white font-semibold' : 'text-gray-500'}>KO</span>
      <span className="text-gray-600">/</span>
      <span className={lang === 'en' ? 'text-white font-semibold' : 'text-gray-500'}>EN</span>
    </button>
  )
}
