from font_service import ensure_font, FONTS, StudioError

if __name__=='__main__':
 for key,meta in FONTS.items():
  try:
   path=ensure_font(key)
   print(f'OK {meta["label"]}: {path.name}')
  except StudioError as exc:print(f'ERROR {meta["label"]}: {exc}')