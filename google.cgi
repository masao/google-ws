#!/usr/local/bin/ruby -w
# -*- Ruby -*-

require 'cgi'
require 'amrita/template'
require 'uconv'
require 'soap/wsdlDriver'

GC.disable

GOOGLE_KEY = File.open("/home/masao/.google_key").read.chomp
GOOGLE_WSDL = 'http://api.google.com/GoogleSearch.wsdl'

EDR_WSDL = 'http://nile.ulis.ac.jp/~masao/term-viz-ws/term-viz.wsdl'

MAX = 10
MAX_PAGE = 20

cgi = CGI.new
print cgi.header("text/html; charset=utf-8")

model = {
   :title => 'Google 検索',
   :result => false,
   :id => '$Id$',
   :key => '',
}

if cgi.has_key?("key") && cgi["key"][0].length > 0
   edr_link = nil
   obj = SOAP::WSDLDriverFactory.new(EDR_WSDL).createDriver
   # obj.resetStream
   # obj.setWireDumpDev(STDERR)
   result = obj.doWordSearch(cgi["key"][0])
   result = result.exactMatchElements
   if result.size > 0
      edr_link = result.collect do |node|
	 wordlist = obj.getWordList(node.idref)
	 wordlist.collect do |word|
	    {
	       :name => word.name,
	       :child => word.child.collect {|node|
		  Amrita::noescape { "<a href=\"javascript:addword('#{node.name}')\">#{node.name}</a> " }
	       },
	       :parent => word.parent.collect {|node|
		  Amrita::noescape { "<a href=\"javascript:addword('#{node.name}')\">#{node.name}</a> " }
	       },
	    }
	 end
      end
   end
   model[:title] << ": #{CGI.escapeHTML(cgi["key"][0])}"
   model[:key] = Amrita::a(:value => CGI.escapeHTML(cgi["key"][0]))

   page = 0
   page = cgi["page"][0].to_i if cgi.has_key?("page")

   google = SOAP::WSDLDriverFactory.new(GOOGLE_WSDL).createDriver
   result = google.doGoogleSearch( GOOGLE_KEY, cgi["key"][0], page * MAX, MAX, false, "", false, "", 'utf-8', 'utf-8' )

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
	    :title => Amrita::e(:a, :href => ele.URL) {
	       Amrita::noescape { ele.title }
	    },
	    :url => Amrita::e(:a, :href => ele.URL) { ele.URL },
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
      :edr_link => edr_link
   }
end

tmpl = Amrita::TemplateFile.new("google.html")
# tmpl.prettyprint = true
tmpl.use_compiler = true
tmpl.expand(STDOUT, model)
