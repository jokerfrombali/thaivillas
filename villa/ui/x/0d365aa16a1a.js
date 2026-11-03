(function(){
  var sec=document.getElementById('section-availability');if(!sec)return;
  var row=sec.querySelector('.flex-nowrap');if(!row)return;
  var MAX_MONTHS=24,ticking=false;

  function addMonth(){
    var months=sec.querySelectorAll('.calendar-month');
    var last=months[months.length-1];
    var off=parseInt(last.getAttribute('data-month-offset'),10);
    if(isNaN(off))off=months.length-1;
    if(off+1>=MAX_MONTHS)return false;
    var clone=last.cloneNode(true);
    clone.setAttribute('data-month-offset',off+1);
    var btns=clone.querySelectorAll('button');
    if(btns[0])btns[0].setAttribute('onclick','prevMonth('+(off+1)+')');
    if(btns[1])btns[1].setAttribute('onclick','nextMonth('+(off+1)+')');
    var grid=clone.querySelector('.calendar-grid');if(grid)grid.innerHTML='';
    row.appendChild(clone);
    if(typeof window.renderCalendars==='function')window.renderCalendars();
    return true;
  }
  function check(){
    ticking=false;
    if(row.scrollWidth<=row.clientWidth+4)return;
    var m=sec.querySelector('.calendar-month');
    var ahead=(m?m.getBoundingClientRect().width:280)*1.2;
    var guard=0;
    while(row.scrollLeft+row.clientWidth>row.scrollWidth-ahead&&guard<3){
      if(!addMonth())break;
      guard++;
    }
  }

  /* swipe hint: a chevron in its own gutter to the right of the strip */
  var next=document.createElement('button');
  next.type='button';
  next.className='thb-cal-next is-hint';
  next.setAttribute('aria-label','Next month');
  next.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5l7 7-7 7"/></svg>';
  sec.appendChild(next);

  function step(){
    var m=sec.querySelector('.calendar-month');
    if(!m)return row.clientWidth;
    var gap=parseFloat(getComputedStyle(row).columnGap||getComputedStyle(row).gap||0)||0;
    return m.getBoundingClientRect().width+gap;
  }
  function place(){
    var r=row.getBoundingClientRect(),s=sec.getBoundingClientRect();
    next.style.top=Math.round(r.top-s.top+r.height/2-19)+'px';
    var atEnd=row.scrollLeft+row.clientWidth>=row.scrollWidth-6;
    next.style.opacity=atEnd?'0':'1';
    next.style.pointerEvents=atEnd?'none':'auto';
  }
  next.addEventListener('click',function(){
    next.classList.remove('is-hint');
    var from=row.scrollLeft;
    var to=Math.min(row.scrollWidth-row.clientWidth,from+step());
    try{row.scrollTo({left:to,behavior:'smooth'});}catch(e){row.scrollLeft=to;}
    /* some browsers ignore programmatic smooth scrolling — make sure it still moves */
    setTimeout(function(){if(Math.abs(row.scrollLeft-from)<2)row.scrollLeft=to;},280);
  });
  row.addEventListener('touchstart',function(){next.classList.remove('is-hint');},{passive:true});

  function onScroll(){if(!ticking){ticking=true;requestAnimationFrame(check);}place();}
  row.addEventListener('scroll',onScroll,{passive:true});
  addEventListener('resize',onScroll);
  addEventListener('load',place);
  setTimeout(place,300);
  place();
})();