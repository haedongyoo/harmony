import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Lang } from '../i18n/translations'

interface LangState {
  lang: Lang
  setLang: (lang: Lang) => void
  toggle: () => void
}

export const useLangStore = create<LangState>()(
  persist(
    (set, get) => ({
      lang: 'ko',
      setLang: (lang) => set({ lang }),
      toggle: () => set({ lang: get().lang === 'ko' ? 'en' : 'ko' }),
    }),
    { name: 'lang' },
  ),
)
