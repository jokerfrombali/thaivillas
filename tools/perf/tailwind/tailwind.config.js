module.exports = {
  // listing pages (villa/, sale/<area>/<slug>/, projects/<slug>/) use villa/ui/main.css, not this file
  content: ['./*.html', './{about,contacts,terms,privacy,saved,vip,villas,property-rental,monthly-rental}/**/*.html',
            './sale/index.html', './sale/*/index.html', './projects/index.html', './*.js', './tools/blog/build.py'],
  theme: { extend: {
    colors: { ink:'#0a0a0a', off:'#fafaf7', paper:'#f2efe8', stone:'#9a9a94', line:'#e6e3dc' },
    fontFamily: { sans:['Inter','system-ui','sans-serif'], display:['Lora','Georgia','serif'] },
    letterSpacing: { tightest:'-0.045em', 'extra-wide':'0.22em' }
  } },
  plugins: [require('@tailwindcss/container-queries')],
}
