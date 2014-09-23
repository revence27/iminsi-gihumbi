$(() ->
  clt = new ClientSide(document)
  clt.activateDates 'activedate'
  deleteableColumns()
  # jigTheElements('.graphicard img', 20)
  condenseNavBar '.collapsiblenav'
  participatingTable '.participant'
  drFridaysDrillDown(document)
)

drFridaysDrillDown = (dest) ->
  for pl in $('.descr')
    play  = $(pl)
    makeDrillable(pl, "subcat=#{play.attr('keyword')}")

makeDrillable = (dr, apdg) ->
  drill = $(dr)
  drill.click(() ->
    return if this.cluck?
    this.cluck = true
    requ  = document.location.toString()
    limb  = if requ.match(/\?/) then '&' else '?'
    sel   = $($('#locations select')[0])
    nom   = sel.attr('name')
    nwtbl = $('<table></table>')
    nwtbl.addClass 'disper'
    $(this).append nwtbl
    for opt in $('option', sel)
      option  = $(opt)
      finu    = "#{requ}#{limb}#{nom}=#{option.val()}&#{apdg}"
      dstd    = $('<td class="numbered"></td>')
      nmtd    = $("<td>#{option.html()}</td>")
      dstr    = $('<tr></tr>')
      dstr.append dstd
      dstr.append nmtd
      nwtbl.append dstr
      makeDrillable nmtd
      $.ajax("#{finu}&summary=on", {
        context: dstd
        success: (dat, stt, xhr) ->
          lk  = $("<a></a>")
          lk.attr 'href', finu.replace('/dashboards/', '/tables/')
          lk.text dat.total
          this.append lk
      })
  )

participatingTable  = (seeker)  ->
  tbl = $(seeker)
  curlk = document.location.toString()
  pcs   = curlk.split('?')[1] or ''
  for tr in $('tr', tbl)
    row = $(tr)
    for td in $('td', row)
      cell  = $(td)
      pn    = cell.attr('partname')
      if pn?
        ncell = $('<td></td>')
        ncell.addClass 'goodtot'
        clink = $('<a>…</a>')
        thelnk  = "#{pcs}&subcat=#{pn}"
        clink.attr('href', "/tables/reports?#{thelnk}")
        ncell.append(clink)
        cell.before(ncell)
        $.ajax("/data/reports?#{thelnk}", {
          # data: parts,
          context: clink,
          success: (dat, stt, xhr) ->
            this.text(dat['total'])
        })

condenseNavBar = (seeker) ->
  nav = $(seeker)
  nnv = $('<a class="navholder">Show Navigation</a>')
  nnv.hide()
  nnv.click(() ->
    nnv.hide('fast', () ->
      nav.show('fast')
    )
  )
  nav.parent().append(nnv)
  nav.hide('slow', () ->
    nnv.show()
  )

jigTheElements = (sel, deg) ->
  dem = $(sel)
  for it in dem
    got = $(it)
    cur = (deg / 2) - Math.floor(Math.random() * deg)
    got.css('transform', "rotate(#{cur}deg)")

deleteableColumns = () ->
  for t, i in $('.largetable thead th')
    td  = $(t)
    hd  = $('<a class="hider" href="javascript://dio.1st.ug/">x</a>')
    hd.attr 'title', "Hide the '#{td.text()}' column"
    hd.attr 'colpos', i
    hd.click((evt) ->
      sth = $(evt.target)
      pos = parseInt(sth.attr('colpos'))
      thd = sth.parent()
      tbl = thd.parent().parent().parent()
      for r in $('tr', tbl)
        for c, x in $('td', r)
          if pos == x
            $(c).hide('fast')
      thd.hide()
    )
    td.append ' '
    td.append hd
