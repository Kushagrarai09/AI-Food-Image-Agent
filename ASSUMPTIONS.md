# Assumptions

1. The free MVP uses Wikimedia Commons as the initial automated image source.
2. The AI acceptance threshold is configurable; 75/100 is the default demo value.
3. Center-cropping is used to create a consistent 1800×1200 output.
4. JPG is the preferred final format because it normally produces a smaller menu-ready file.
5. Rejected candidates are automatically skipped and the next candidate is evaluated.
6. Difficult food names are sent to the image search provider as supplied, with `food` and `dish` query variants as fallbacks.
7. Google Drive access is authorized through OAuth; credentials are never committed to GitHub.
8. Source URL, license and author are recorded where the source API provides them.
9. The agent continues processing other food items after an individual item fails.
10. The free search provider is an MVP choice; a production deployment may replace it with a provider whose API/terms fit the restaurant's use case.
