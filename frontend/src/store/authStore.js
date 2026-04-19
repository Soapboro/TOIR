import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const useAuthStore = create(
  persist(
    (set) => ({
      user: null,
      token: null,
      refreshToken: null,

      setAuth: (user, access, refresh) =>
        set({ user, token: access, refreshToken: refresh }),

      setAccessToken: (access) =>
        set({ token: access }),

      logout: () =>
        set({ user: null, token: null, refreshToken: null }),
    }),
    { name: 'toir-auth' }
  )
);

export default useAuthStore;
