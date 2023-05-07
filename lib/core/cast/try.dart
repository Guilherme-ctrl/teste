T tryCast<T>(dynamic value, T fallback) {
  try {
    return value as T;
  } catch (e) {
    return fallback;
  }
}
