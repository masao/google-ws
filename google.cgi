#!/usr/local/bin/ruby -wT
# -*- Ruby -*-

require 'cgi'
require 'amrita/template'
require 'uconv'
require 'soap/wsdlDriver'

include Amrita

GOOGLE_KEY = File.open("/home/masao/.google_key").read.chomp
GOOGLE_WSDL = 'http://api.google.com/GoogleSearch.wsdl'

MAX = 10
MAX_PAGE = 20

cgi = CGI.new
print cgi.header("text/html; charset=utf-8")

model = {
   :title => 'Gooogle 検索',
   :result => false,
   :id => '$Id$',
}

if cgi.has_key?("key") && cgi["key"][0].length > 0
   model[:title] += ": #{CGI.escapeHTML(cgi["key"][0])}"
   model[:key] = a(:value => CGI.escapeHTML(cgi["key"][0]))

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
      :start => result.startIndex,
      :end => result.endIndex,
      :search_result => result.resultElements.collect do |ele|
	 {
	    :title => e(:a, :href => ele.URL) { noescape { ele.title } },
	    :url => e(:a, :href => ele.URL) { ele.URL },
	    :snippet => noescape { ele.snippet },
	    :count => count += 1,
	 }
      end,
      :page_list => (first_page .. last_page).collect do |i|
	 if i == page
	    "[#{i+1}]\n"
	 else
	    e(:a, :href => "#{base_url};page=#{i}") { "[#{i+1}]" } + "\n"
	 end
      end,
      :is_first_page => first_page == 0 ? false : "... ",
      :is_last_page => last_page * MAX > result.estimatedTotalResultsCount ? false : "... ",
   }
end

tmpl = TemplateFile.new("google.html")
# tmpl.prettyprint = true
tmpl.expand(STDOUT, model)
