#!/usr/local/bin/ruby
# -*- Ruby -*-

require 'cgi'
require 'amrita/template'
require 'uconv'
require 'soap/wsdlDriver'

$:.unshift "."
require 'util'

GC.disable

GOOGLE_KEY = File.open("/home/masao/.google_key").read.chomp
GOOGLE_WSDL = 'http://api.google.com/GoogleSearch.wsdl'

TERM_WSDL = {
   'edr' => TermWSDL::new("EDR", 'http://nile.ulis.ac.jp/~masao/term-viz-ws/edr/term.wsdl'),
   'odp' => TermWSDL::new("ODP", 'http://nile.ulis.ac.jp/~masao/term-viz-ws/odp/term.wsdl')
}

MAX = 10
MAX_PAGE = 20

cgi = CGI.new

model = {
   :title => 'Google 検索',
   :result => false,
   :id => '$Id$',
   :key => '',
}

if cgi.valid?( "key" ) then
	boundary = 'google_cgi'
	# 時間がかかる処理になるので、multipart/x-mixed-replace で
	# ブラウザに渡しておく。
	print cgi.header( "multipart/x-mixed-replace;boundary=#{boundary}" )
	puts "--#{boundary}"
	print cgi.header( 'text/html; charset=utf-8' )
	model[:message] = '検索処理中です。しばらくお待ちください。'
	tmpl = Amrita::TemplateFile.new("google.html")
	tmpl.expand(STDOUT, model)
	model[:message] = nil
	puts "--#{boundary}"
	
   term_link = []
   TERM_WSDL.keys.each do |key|
      obj = SOAP::WSDLDriverFactory.new(TERM_WSDL[key].wsdl).createDriver
      STDERR.puts "#{TERM_WSDL[key].name} - creatDriver done."
      # obj.resetStream
      # obj.setWireDumpDev(STDERR)
      match = obj.doWordSearch(cgi["key"][0]).exactMatchElements
      STDERR.puts "obj.doWordSearch done."
      unless match.empty? then
	 STDERR.puts " #{TERM_WSDL[key].name} - #{match.size} found!!"
	 term_link << match.collect do |node|
	    wordlist = obj.getWordList(node.idref)
	    wordlist.collect do |word|
	       {
		  :term_name => TERM_WSDL[key].name,
		  :name => word.name,
		  :child => word.child.collect {|c|
		     Amrita::noescape { "<a href=\"javascript:addword('#{c.name}')\">#{c.name}</a> " }
		  },
		  :parent => word.parent.collect {|p|
		     Amrita::noescape { "<a href=\"javascript:addword('#{p.name}')\">#{p.name}</a> " }
		  }
	       }
	    end
	 end
      end
   end

   STDERR.puts "-- term_link created --"

   model[:title] << ": #{CGI.escapeHTML(cgi["key"][0])}"
   model[:key] = Amrita::a(:value => CGI.escapeHTML(cgi["key"][0]))

   page = 0
   page = cgi["page"][0].to_i if cgi.valid?( "page" )

   google = SOAP::WSDLDriverFactory.new(GOOGLE_WSDL).createDriver
   STDERR.puts "Google - createDriver done."
   google.resetStream
   google.setWireDumpDev(File.open("/tmp/google_cgi.#{$$}", "w"))
   result = google.doGoogleSearch( GOOGLE_KEY, cgi["key"][0], page * MAX, MAX, false, "", false, "", 'utf-8', 'utf-8' )
   STDERR.puts "google.doGoogleSearch done."

   count = result.startIndex - 1

   first_page = page - MAX_PAGE / 2
   first_page = 0 if first_page < 0

   last_page = result.estimatedTotalResultsCount / MAX
   last_page = page + MAX_PAGE / 2 if last_page - first_page > MAX_PAGE

   base_url = "google.cgi?key=#{CGI.escape(cgi["key"][0])}"

   model[:result] = {
      :count => result.estimatedTotalResultsCount,
      :estimate_is_exact => result.estimateIsExact ? false : "約",
      :start => result.startIndex,
      :end => result.endIndex,
      :search_time => sprintf("%.02f", result.searchTime),
      :search_comments => result.searchComments,
      :search_tips => result.searchTips,
      :search_result => result.resultElements.collect do |ele|
	 {
	    :title => Amrita::e(:a, :href => ele.URL ) {
	       Amrita::noescape { ele.title }
	    },
	    :url => Amrita::e(:a, :href => ele.URL ) { ele.URL },
	    :snippet => Amrita::noescape { ele.snippet },
	    :count => count += 1,
	 }
      end,
      :page_list => (first_page .. last_page).collect do |i|
	 if i == page
	    "[#{i+1}]\n"
	 else
	    Amrita::e(:a, :href => "#{base_url};page=#{i}") { "[#{i+1}]" } + "\n"
	 end
      end,
      :is_first_page => first_page == 0 ? false : "... ",
      :is_last_page => last_page * MAX > result.estimatedTotalResultsCount ? false : "... ",
      :term_link => term_link
   }
end

print cgi.header( 'text/html; charset=utf-8' )
tmpl = Amrita::TemplateFile.new("google.html")
# tmpl.prettyprint = true
# tmpl.use_compiler = true
tmpl.expand(STDOUT, model)

puts "--#{boundary}--" if cgi.valid?( "key" )
